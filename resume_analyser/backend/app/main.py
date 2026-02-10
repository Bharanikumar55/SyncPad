from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from pdf2image import convert_from_path
import os
import uuid
import requests
import re
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-25.07.0\poppler-25.07.0\Library\bin"

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Hugging Face Configuration
HF_API_KEY = os.getenv("HF_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

app = FastAPI(title="Interview Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000","http://localhost:5173","http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database in production)
resume_data_store = {}

def extract_text_from_file(file_path: str) -> str:
    """Extract text from image or PDF file"""
    text = ""
    
    try:
        if file_path.lower().endswith(".pdf"):
            pages = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
            for i, page in enumerate(pages):
                img_path = f"temp_{uuid.uuid4()}.png"
                page.save(img_path, "PNG")
                page_text = pytesseract.image_to_string(img_path)
                text += f"Page {i+1}:\n{page_text}\n\n"
                os.remove(img_path)
        else:
            text = pytesseract.image_to_string(file_path)

        return text.strip()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

def download_from_cloudinary(public_id: str, original_filename: str) -> str:
    """Download file from Cloudinary with correct resource type detection"""
    try:
        print(f"Downloading from Cloudinary with public_id: {public_id}")
        print(f"Original filename: {original_filename}")
        
        # Determine resource type based on file extension
        if original_filename.lower().endswith('.pdf'):
            resource_type = "raw"  # PDFs are raw files
            ext = '.pdf'
            # For PDFs, use a simpler URL without transformation flags
            download_url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                type="upload"
            )[0]
        else:
            resource_type = "image"  # Images
            ext = '.png'
            download_url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                type="upload",
                flags="attachment"
            )[0]
        
        print(f"Resource type: {resource_type}")
        print(f"Generated download URL: {download_url}")
        
        temp_file = f"cloudinary_{uuid.uuid4()}{ext}"
        
        # Download the file
        response = requests.get(download_url)
        print(f"Download response status: {response.status_code}")
        
        if response.status_code != 200:
            # Try alternative URL without flags
            if resource_type == "raw":
                alt_url = f"https://res.cloudinary.com/dgiomhyja/raw/upload/{public_id}"
            else:
                alt_url = f"https://res.cloudinary.com/dgiomhyja/image/upload/{public_id}"
            
            print(f"Trying alternative URL: {alt_url}")
            response = requests.get(alt_url)
            response.raise_for_status()
        
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(temp_file)
        print(f"Downloaded file size: {file_size} bytes")
        
        # Verify file is not empty
        if file_size == 0:
            raise Exception("Downloaded file is empty")
            
        return temp_file
        
    except Exception as e:
        print(f"Cloudinary download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download from Cloudinary: {str(e)}")
def summarize_with_huggingface(text: str) -> str:
    """Summarize text using Hugging Face BART API"""
    try:
        payload = {
            "inputs": text[:2000],
            "parameters": {
                "max_length": 150,
                "min_length": 40,
                "do_sample": False,
            }
        }
        
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            HF_API_URL, 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                if 'summary_text' in result[0]:
                    return result[0]['summary_text']
            elif isinstance(result, dict) and 'summary_text' in result:
                return result['summary_text']
                
        return None  # Return None if API fails
            
    except Exception as e:
        print(f"Hugging Face API error: {str(e)}")
        return None

def extract_skills_advanced(text: str) -> list:
    """Extract technical skills from resume text"""
    skill_patterns = {
        'Programming': ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'],
        'Frontend': ['react', 'angular', 'vue', 'typescript', 'html', 'css', 'sass', 'bootstrap', 'tailwind'],
        'Backend': ['node.js', 'django', 'flask', 'spring', 'express', 'fastapi', 'laravel', 'rails'],
        'Database': ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server'],
        'Cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform', 'ci/cd'],
        'Data Science': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'nlp'],
        'Mobile': ['android', 'ios', 'react native', 'flutter', 'swift'],
        'Tools': ['git', 'linux', 'bash', 'jira', 'confluence', 'figma']
    }
    
    text_lower = text.lower()
    detected_skills = []
    
    for category, skills in skill_patterns.items():
        for skill in skills:
            if skill in text_lower:
                pretty_skill = skill.title()
                if skill == 'node.js':
                    pretty_skill = 'Node.js'
                elif skill == 'ci/cd':
                    pretty_skill = 'CI/CD'
                detected_skills.append(pretty_skill)
    
    return list(set(detected_skills))

def extract_experience_level(text: str) -> str:
    """Extract experience level from text"""
    text_lower = text.lower()
    
    senior_keywords = {'senior', 'lead', 'principal', 'architect', 'manager', 'head of', 'team lead'}
    junior_keywords = {'junior', 'entry', 'fresher', 'intern', 'trainee', 'graduate'}
    
    senior_count = sum(1 for keyword in senior_keywords if keyword in text_lower)
    junior_count = sum(1 for keyword in junior_keywords if keyword in text_lower)
    
    if senior_count > junior_count:
        return "Senior"
    elif junior_count > senior_count:
        return "Junior"
    else:
        return "Mid-Level"

def extract_experience_years(text: str) -> int:
    """Extract years of experience"""
    patterns = [r'(\d+)\+?\s*years?', r'(\d+)\+?\s*yrs?', r'experience.*?(\d+)\+?']
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            years = [int(match) for match in matches]
            return max(years)
    
    # Estimate based on keywords
    text_lower = text.lower()
    if any(word in text_lower for word in ['senior', 'lead', 'principal', '10+', '15+', '20+']):
        return 8
    elif any(word in text_lower for word in ['mid-level', 'mid level', '5+', '7+']):
        return 5
    elif any(word in text_lower for word in ['junior', 'entry', 'fresher', '0-2', '1-2']):
        return 1
    else:
        return 3

def recommend_difficulty(experience_level: str, skills_count: int, years_exp: int) -> str:
    """Recommend problem difficulty"""
    if (experience_level == "Senior" and skills_count >= 5) or years_exp >= 8:
        return "Hard"
    elif experience_level == "Junior" or skills_count <= 2 or years_exp <= 2:
        return "Easy"
    else:
        return "Medium"

def generate_smart_summary(skills: list, experience_level: str, years_exp: int) -> str:
    """Generate smart summary without external API"""
    if experience_level == "Senior" and len(skills) >= 5:
        return f"Experienced {experience_level} professional with {years_exp}+ years of expertise in {', '.join(skills[:3])}. Strong background in system architecture, team leadership, and scalable solutions."
    elif experience_level == "Junior":
        return f"{experience_level} level candidate with {years_exp} years of experience in {', '.join(skills[:3]) if skills else 'programming'}. Strong foundation in computer science fundamentals and eager to learn new technologies."
    else:
        return f"{experience_level} level professional with {years_exp} years of solid experience in {', '.join(skills[:3]) if skills else 'software development'}. Proven track record in building robust applications and solving complex problems."

def generate_resume_summary(extracted_text: str) -> dict:
    """Generate complete resume summary"""
    print("Starting resume analysis...")
    
    # Extract basic information
    skills = extract_skills_advanced(extracted_text)
    experience_level = extract_experience_level(extracted_text)
    years_exp = extract_experience_years(extracted_text)
    difficulty = recommend_difficulty(experience_level, len(skills), years_exp)
    
    print(f"Extracted {len(skills)} skills")
    print(f"Experience: {experience_level}, Years: {years_exp}")
    
    # Try Hugging Face API first
    ai_summary = summarize_with_huggingface(extracted_text)
    
    if ai_summary:
        professional_summary = ai_summary
        summary_source = "AI Analysis (BART)"
        print("Using AI summary")
    else:
        professional_summary = generate_smart_summary(skills, experience_level, years_exp)
        summary_source = "Smart Rule-Based Analysis"
        print("Using rule-based summary")
    
    return {
        "professional_summary": professional_summary,
        "key_skills": skills[:10],
        "experience_level": experience_level,
        "experience_years": years_exp,
        "recommended_difficulty": difficulty,
        "technical_strengths": skills[:5] if skills else ["Problem Solving", "Software Development"],
        "interview_focus": skills[:3] if skills else ["Data Structures", "Algorithms", "System Design"],
        "summary_source": summary_source,
        "skills_count": len(skills)
    }

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Candidate uploads resume - store in Cloudinary and auto-summarize"""
    try:
        allowed_types = ['.pdf', '.png', '.jpg', '.jpeg']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Save temporary file
        temp_file = f"upload_{uuid.uuid4()}{ext}"
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"Step 1: Uploading to Cloudinary...")
        # Upload to Cloudinary
        cloudinary_response = cloudinary.uploader.upload(
            temp_file, 
            folder="interview_resumes",
            resource_type="auto"
        )
        
        print(f"Step 2: Extracting text with OCR...")
        # Extract text using OCR (use the local file for faster processing)
        extracted_text = extract_text_from_file(temp_file)
        print(f"Extracted {len(extracted_text)} characters")
        
        print(f"Step 3: Generating AI summary...")
        # Generate summary immediately
        summary = generate_resume_summary(extracted_text)
        print("Summary generated successfully!")
        
        # Generate resume ID
        resume_id = str(uuid.uuid4())
        
        # Store data with summary
        resume_data_store[resume_id] = {
            "file_name": file.filename,
            "cloudinary_url": cloudinary_response['secure_url'],
            "public_id": cloudinary_response['public_id'],
            "uploaded_at": str(os.path.getctime(temp_file)),
            "summary": summary,
            "extracted_text": extracted_text,
            "status": "analyzed"
        }
        
        # Cleanup
        os.remove(temp_file)
        
        return {
            "resume_id": resume_id,
            "message": "Resume uploaded and analyzed successfully",
            "cloudinary_url": cloudinary_response['secure_url'],
            "public_id": cloudinary_response['public_id'],
            "summary": summary,
            "text_preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
            "status": "uploaded_and_analyzed"
        }

    except Exception as e:
        # Cleanup temp file if it exists
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
        return {"error": str(e)}

@app.post("/analyze-resume/{resume_id}")
async def analyze_resume(resume_id: str):
    """Interviewer clicks summarize - OCR + AI analysis happens"""
    try:
        print(f"=== Starting analysis for resume: {resume_id} ===")
        
        if resume_id not in resume_data_store:
            print(f"Resume {resume_id} not found in storage")
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resume_data_store[resume_id]
        print(f"Found resume: {resume_data['file_name']}")
        
        # Download from Cloudinary USING PUBLIC_ID AND FILENAME
        print("Step 1: Downloading from Cloudinary...")
        try:
            temp_file = download_from_cloudinary(
                resume_data["public_id"], 
                resume_data["file_name"]
            )
            print(f"Downloaded to: {temp_file}")
        except Exception as e:
            print(f"Cloudinary download failed: {str(e)}")
            return {"error": f"Cloudinary download failed: {str(e)}"}
        
        # ... [rest of your existing code] ...
        # Extract text using OCR
        print("Step 2: Extracting text with OCR...")
        try:
            extracted_text = extract_text_from_file(temp_file)
            print(f"Extracted text length: {len(extracted_text)}")
            if not extracted_text or len(extracted_text.strip()) == 0:
                print("WARNING: No text extracted from file!")
        except Exception as e:
            print(f"OCR extraction failed: {str(e)}")
            # Cleanup temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {"error": f"OCR extraction failed: {str(e)}"}
        
        # Generate summary
        print("Step 3: Generating summary...")
        try:
            summary = generate_resume_summary(extracted_text)
            print("Summary generated successfully")
        except Exception as e:
            print(f"Summary generation failed: {str(e)}")
            # Cleanup temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return {"error": f"Summary generation failed: {str(e)}"}
        
        # Update resume data
        resume_data_store[resume_id]["extracted_text"] = extracted_text
        resume_data_store[resume_id]["summary"] = summary
        resume_data_store[resume_id]["status"] = "analyzed"
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print("Temporary file cleaned up")
        
        print("=== Analysis completed successfully ===")
        
        return {
            "resume_id": resume_id,
            "summary": summary,
            "text_preview": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
            "status": "analysis_complete"
        }
        
    except Exception as e:
        print(f"=== ANALYSIS FAILED: {str(e)} ===")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {"error": str(e)}

@app.get("/resume/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume data for interviewer view"""
    if resume_id not in resume_data_store:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resume_data_store[resume_id]
    
    return {
        "resume_id": resume_id,
        "file_name": resume_data["file_name"],
        "cloudinary_url": resume_data["cloudinary_url"],
        "status": resume_data["status"],
        "has_summary": resume_data["summary"] is not None,
        "summary": resume_data["summary"],
        "uploaded_at": resume_data["uploaded_at"],
        "text_preview": resume_data["extracted_text"][:200] + "..." if resume_data["extracted_text"] and len(resume_data["extracted_text"]) > 200 else resume_data.get("extracted_text", "")
    }

@app.get("/resumes")
async def list_resumes():
    """List all uploaded resumes"""
    resumes = []
    for resume_id, data in resume_data_store.items():
        resumes.append({
            "resume_id": resume_id,
            "file_name": data["file_name"],
            "cloudinary_url": data["cloudinary_url"],
            "status": data["status"],
            "has_summary": data["summary"] is not None
        })
    
    return {"resumes": resumes}

@app.delete("/resume/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete resume from Cloudinary and local storage"""
    try:
        if resume_id not in resume_data_store:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        resume_data = resume_data_store[resume_id]
        
        # Delete from Cloudinary
        cloudinary.uploader.destroy(resume_data["public_id"])
        
        # Remove from local storage
        del resume_data_store[resume_id]
        
        return {
            "message": "Resume deleted successfully",
            "resume_id": resume_id
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-upload")
async def test_upload():
    """Test Cloudinary connection"""
    try:
        # Upload a test file
        test_response = cloudinary.uploader.upload(
            "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            folder="test_interview"
        )
        
        return {
            "status": "success",
            "cloudinary_url": test_response['secure_url'],
            "message": "Cloudinary is working!"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Interview Platform API - Resume Analysis with Cloudinary"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)