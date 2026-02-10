import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ResumeViewer = ({ resumeId }) => {
    const [resumeData, setResumeData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        if (resumeId) {
            fetchResumeData();
        }
    }, [resumeId]);

    const fetchResumeData = async () => {
        try {
            const response = await axios.get(`http://localhost:8000/resume/${resumeId}`);
            setResumeData(response.data);
        } catch (error) {
            console.error('Failed to fetch resume:', error);
        }
    };

    const handleAnalyze = async () => {
        setAnalyzing(true);
        try {
            const response = await axios.post(`http://localhost:8000/analyze-resume/${resumeId}`);
            setResumeData(prev => ({
                ...prev,
                summary: response.data.summary,
                status: 'analyzed'
            }));
        } catch (error) {
            console.error('Analysis failed:', error);
            alert('Analysis failed: ' + error.response?.data?.error);
        }
        setAnalyzing(false);
    };

    if (!resumeData) {
        return <div>Loading resume...</div>;
    }

    return (
        <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
            {/* Header with Analyze Button */}
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '20px',
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #dee2e6'
            }}>
                <div>
                    <h2>Candidate Resume: {resumeData.file_name}</h2>
                    <p style={{ margin: 0, color: '#6c757d' }}>
                        Status: <strong>{resumeData.status}</strong>
                    </p>
                </div>
                
                {!resumeData.has_summary && (
                    <button 
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        style={{
                            padding: '12px 24px',
                            backgroundColor: analyzing ? '#6c757d' : '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: analyzing ? 'not-allowed' : 'pointer',
                            fontSize: '16px',
                            fontWeight: 'bold'
                        }}
                    >
                        {analyzing ? '🔍 Analyzing...' : '📊 Analyze & Summarize'}
                    </button>
                )}
            </div>

            {/* Resume Display */}
            <div style={{ marginBottom: '30px' }}>
                <h3>Resume Preview</h3>
                <div style={{ 
                    border: '2px solid #e9ecef', 
                    borderRadius: '8px',
                    padding: '10px',
                    backgroundColor: 'white'
                }}>
                    {resumeData.cloudinary_url.includes('.pdf') ? (
                        <iframe 
                            src={resumeData.cloudinary_url} 
                            width="100%" 
                            height="600px"
                            style={{ border: 'none', borderRadius: '4px' }}
                            title="Resume PDF"
                        />
                    ) : (
                        <img 
                            src={resumeData.cloudinary_url} 
                            alt="Resume" 
                            style={{ 
                                maxWidth: '100%', 
                                border: '1px solid #ddd',
                                borderRadius: '4px'
                            }}
                        />
                    )}
                </div>
            </div>

            {/* Summary Display */}
            {resumeData.has_summary && resumeData.summary && (
                <div style={{ 
                    padding: '25px', 
                    backgroundColor: '#e8f5e8', 
                    borderRadius: '8px',
                    border: '2px solid #28a745'
                }}>
                    <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        marginBottom: '20px'
                    }}>
                        <h3 style={{ color: '#155724', margin: 0 }}>📋 Resume Analysis</h3>
                        <span style={{ 
                            padding: '4px 12px', 
                            backgroundColor: '#28a745', 
                            color: 'white',
                            borderRadius: '20px',
                            fontSize: '14px'
                        }}>
                            {resumeData.summary.summary_source}
                        </span>
                    </div>

                    {/* Professional Summary */}
                    <div style={{ marginBottom: '20px' }}>
                        <h4 style={{ color: '#155724' }}>Professional Summary</h4>
                        <p style={{ 
                            fontSize: '16px', 
                            lineHeight: '1.6',
                            backgroundColor: 'white',
                            padding: '15px',
                            borderRadius: '6px',
                            borderLeft: '4px solid #007bff'
                        }}>
                            {resumeData.summary.professional_summary}
                        </p>
                    </div>

                    {/* Key Information Grid */}
                    <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                        gap: '15px',
                        marginBottom: '20px'
                    }}>
                        <div style={{ 
                            backgroundColor: 'white', 
                            padding: '15px', 
                            borderRadius: '6px',
                            border: '1px solid #dee2e6'
                        }}>
                            <strong>Experience Level</strong>
                            <p style={{ margin: '5px 0 0 0', fontSize: '18px', color: '#007bff' }}>
                                {resumeData.summary.experience_level} ({resumeData.summary.experience_years} years)
                            </p>
                        </div>
                        
                        <div style={{ 
                            backgroundColor: 'white', 
                            padding: '15px', 
                            borderRadius: '6px',
                            border: '1px solid #dee2e6'
                        }}>
                            <strong>Recommended Difficulty</strong>
                            <p style={{ 
                                margin: '5px 0 0 0', 
                                fontSize: '18px', 
                                color: resumeData.summary.recommended_difficulty === 'Hard' ? '#dc3545' : 
                                       resumeData.summary.recommended_difficulty === 'Medium' ? '#ffc107' : '#28a745',
                                fontWeight: 'bold'
                            }}>
                                {resumeData.summary.recommended_difficulty}
                            </p>
                        </div>
                        
                        <div style={{ 
                            backgroundColor: 'white', 
                            padding: '15px', 
                            borderRadius: '6px',
                            border: '1px solid #dee2e6'
                        }}>
                            <strong>Skills Found</strong>
                            <p style={{ margin: '5px 0 0 0', fontSize: '18px', color: '#007bff' }}>
                                {resumeData.summary.skills_count} skills
                            </p>
                        </div>
                    </div>

                    {/* Key Skills */}
                    <div style={{ marginBottom: '20px' }}>
                        <h4 style={{ color: '#155724' }}>Key Skills</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {resumeData.summary.key_skills.map((skill, index) => (
                                <span 
                                    key={index}
                                    style={{
                                        padding: '6px 12px',
                                        backgroundColor: '#007bff',
                                        color: 'white',
                                        borderRadius: '20px',
                                        fontSize: '14px'
                                    }}
                                >
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Interview Focus Areas */}
                    <div style={{ marginBottom: '20px' }}>
                        <h4 style={{ color: '#155724' }}>🎯 Interview Focus Areas</h4>
                        <ul style={{ 
                            backgroundColor: 'white', 
                            padding: '15px 15px 15px 30px', 
                            borderRadius: '6px',
                            border: '1px solid #dee2e6'
                        }}>
                            {resumeData.summary.interview_focus.map((area, index) => (
                                <li key={index} style={{ marginBottom: '8px', fontSize: '15px' }}>
                                    {area}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Technical Strengths */}
                    <div>
                        <h4 style={{ color: '#155724' }}>💪 Technical Strengths</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {resumeData.summary.technical_strengths.map((strength, index) => (
                                <span 
                                    key={index}
                                    style={{
                                        padding: '6px 12px',
                                        backgroundColor: '#28a745',
                                        color: 'white',
                                        borderRadius: '20px',
                                        fontSize: '14px'
                                    }}
                                >
                                    {strength}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResumeViewer;