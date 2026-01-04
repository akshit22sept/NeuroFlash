import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import SliceGallery from './components/SliceGallery';



const API_BASE = 'http://localhost:8000/api';

interface ProcessingState {
  isProcessing: boolean;
  progress: number;
  stage: string;
  fileId: string | null;
  error?: string;
}

interface Sample {
  id: string;
  filename: string;
  name: string;
  description: string;
  type: string;
  severity: string;
  exists: boolean;
}

interface AnalysisResults {
  file_id: string;
  filename: string;
  timestamp: string;
  analysis: {
    metrics: {
      stroke_voxels: number;
      stroke_volume_mm3: number;
      stroke_volume_cm3: number;
      brain_percentage: number;
      severity: string;
      severity_score: number;
      has_stroke: boolean;
    };
    ai_explanation: {
      explanation: string;
      confidence: number;
      model: string;
    } | null;

    most_affected_slices?: Array<{
      slice_num: number;
      lesion_voxels: number;
      stroke_voxels: number;
      hemorrhage_voxels: number;
    }>;
  };
  brain_mesh?: {
    vertices: number[][];
    faces: number[][];
    normals: number[][];
  };
  stroke_mesh?: {
    vertices: number[][];
    faces: number[][];
    normals: number[][];
  };
  hemorrhage_mesh?: {
    vertices: number[][];
    faces: number[][];
    normals: number[][];
  };
  visualization_url?: string;
}

function App() {
  const [processingState, setProcessingState] = useState<ProcessingState>({
    isProcessing: false,
    progress: 0,
    stage: '',
    fileId: null
  });
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [samplesLoading, setSamplesLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load available samples on component mount
  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const response = await axios.get(`${API_BASE}/available-scans`);
        setSamples(response.data.scans);
      } catch (error) {
        console.error('Failed to load samples:', error);
        setSamples([]);
      } finally {
        setSamplesLoading(false);
      }
    };

    fetchSamples();
  }, []);

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Clear previous results
      setResults(null);

      setProcessingState({
        isProcessing: true,
        progress: 10,
        stage: 'uploading',
        fileId: null
      });

      const response = await axios.post(`${API_BASE}/process-scan`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const fileId = response.data.file_id;
      setProcessingState(prev => ({ ...prev, fileId, stage: 'processing', progress: 30 }));

      // Poll for results
      await pollForResults(fileId);
    } catch (error) {
      setProcessingState({
        isProcessing: false,
        progress: 0,
        stage: 'error',
        fileId: null,
        error: error instanceof Error ? error.message : 'Upload failed'
      });
    }
  };

  const pollForResults = async (fileId: string) => {
    const maxAttempts = 120; // 4 minutes max
    let attempts = 0;

    const poll = async (): Promise<void> => {
      try {
        const response = await axios.get(`${API_BASE}/status/${fileId}`);
        const data = response.data;

        // Check for error first
        if (data.status === 'error' || data.error) {
          setProcessingState({
            isProcessing: false,
            progress: 0,
            stage: 'error',
            fileId: null,
            error: data.error || 'Processing failed on the server'
          });
          console.error('Backend processing error:', data);
          return;
        }

        if ('analysis' in data) {
          // Complete results
          setResults(data);
          setProcessingState({
            isProcessing: false,
            progress: 100,
            stage: 'completed',
            fileId: null
          });
          console.log('Processing complete:', data);
          return;
        }

        // Still processing
        setProcessingState(prev => ({
          ...prev,
          progress: Math.min(95, 30 + (attempts * 0.5)),
          stage: data.stage || 'processing'
        }));

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          throw new Error('Processing timeout - exceeded 4 minutes');
        }
      } catch (error) {
        setProcessingState({
          isProcessing: false,
          progress: 0,
          stage: 'error',
          fileId: null,
          error: error instanceof Error ? error.message : 'Processing failed'
        });
        console.error('Polling error:', error);
      }
    };

    poll();
  };

  const handleDemoScan = async (filename: string) => {
    try {
      console.log('Processing demo scan:', filename);

      // Clear previous results
      setResults(null);

      setProcessingState({
        isProcessing: true,
        progress: 20,
        stage: 'loading demo',
        fileId: null
      });

      console.log('Calling API:', `${API_BASE}/process-demo-scan?filename=${filename}`);
      const response = await axios.post(`${API_BASE}/process-demo-scan`, null, {
        params: { filename }
      });

      console.log('Demo scan response:', response.data);
      const fileId = response.data.file_id;
      setProcessingState(prev => ({ ...prev, fileId, stage: 'processing', progress: 40 }));

      await pollForResults(fileId);
    } catch (error: any) {
      console.error('Demo scan error:', error);
      console.error('Error response:', error.response?.data);
      setProcessingState({
        isProcessing: false,
        progress: 0,
        stage: 'error',
        fileId: null,
        error: error.response?.data?.detail || error.message || 'Demo processing failed'
      });
    }
  };

  const formatVolume = (volume: number) => {
    if (volume < 1000) return `${volume.toFixed(1)} mm³`;
    return `${(volume / 1000).toFixed(1)} cm³`;
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#f1f5f9',
      fontFamily: 'system-ui, sans-serif'
    }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, #1e293b, #374151)',
        borderBottom: '1px solid #374151',
        padding: '2rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '4rem',
              height: '4rem',
              background: 'linear-gradient(135deg, #1e40af, #3b82f6)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '2rem'
            }}>🧠</div>
            <div>
              <h1 style={{ margin: 0, fontSize: '2.5rem', fontWeight: 'bold' }}>NeuroFlash</h1>
              <p style={{ margin: 0, color: '#9ca3af' }}>Advanced Brain Damage Segmentation</p>
            </div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem' }}>

          {/* Upload Section */}
          <div style={{
            background: 'linear-gradient(135deg, #1e293b, #334155)',
            border: '1px solid #374151',
            borderRadius: '12px',
            padding: '2rem',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)'
          }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.3rem' }}>📤 Upload Brain Scan</h3>

            <div
              style={{
                border: '2px dashed #374151',
                borderRadius: '8px',
                padding: '2rem',
                textAlign: 'center',
                cursor: processingState.isProcessing ? 'not-allowed' : 'pointer',
                opacity: processingState.isProcessing ? 0.5 : 1,
                transition: 'all 0.2s'
              }}
              onClick={() => !processingState.isProcessing && fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (!processingState.isProcessing && e.dataTransfer.files[0]) {
                  handleFileUpload(e.dataTransfer.files[0]);
                }
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".nii,.nii.gz"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
              />
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📤</div>
              <p>Drag & drop brain scan or click to browse</p>
              <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.5rem' }}>
                Supported: .nii, .nii.gz files
              </p>
            </div>

            {/* Demo Scans */}
            <div style={{ marginTop: '1.5rem' }}>
              <h4 style={{ margin: '0 0 1rem 0', color: '#d1d5db' }}>🧪 Try Demo Scans</h4>
              {samplesLoading ? (
                <div style={{ color: '#9ca3af', textAlign: 'center', padding: '1rem' }}>
                  Loading samples...
                </div>
              ) : samples.length === 0 ? (
                <div style={{ color: '#ef4444', fontSize: '0.9rem' }}>
                  ⚠️ No demo samples available
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {samples.map((sample) => (
                    <button
                      key={sample.id}
                      onClick={() => !processingState.isProcessing && !sample.exists ? undefined : handleDemoScan(sample.filename)}
                      disabled={processingState.isProcessing || !sample.exists}
                      title={sample.exists ? sample.description : `File not found: ${sample.filename}`}
                      style={{
                        padding: '0.75rem 1rem',
                        background: !sample.exists
                          ? '#4b5563'
                          : processingState.isProcessing
                            ? '#374151'
                            : '#4b5563',
                        border: `1px solid ${!sample.exists ? '#6b4b4b' : '#6b7280'}`,
                        borderRadius: '6px',
                        color: !sample.exists ? '#9ca3af' : 'white',
                        cursor: processingState.isProcessing || !sample.exists ? 'not-allowed' : 'pointer',
                        transition: 'background 0.2s',
                        textAlign: 'left',
                        opacity: !sample.exists ? 0.6 : 1
                      }}
                    >
                      <div style={{ fontWeight: '500' }}>
                        🧠 {sample.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: !sample.exists ? '#6b4b4b' : '#d1d5db', marginTop: '0.25rem' }}>
                        {sample.description}
                        {!sample.exists && ' [FILE NOT FOUND]'}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Processing Status */}
          {processingState.isProcessing && (
            <div style={{
              background: 'linear-gradient(135deg, #1e293b, #334155)',
              border: '1px solid #374151',
              borderRadius: '12px',
              padding: '2rem'
            }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.3rem' }}>⚡ Processing Status</h3>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span>{processingState.stage}</span>
                  <span>{processingState.progress}%</span>
                </div>
                <div style={{
                  width: '100%',
                  height: '8px',
                  background: '#374151',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${processingState.progress}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #1e40af, #3b82f6)',
                    transition: 'width 0.3s'
                  }} />
                </div>
              </div>

              {processingState.error && (
                <div style={{
                  padding: '1rem',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px',
                  color: '#fca5a5'
                }}>
                  ❌ {processingState.error}
                </div>
              )}
            </div>
          )}

          {/* Results */}
          {results && (
            <div style={{
              background: 'linear-gradient(135deg, #1e293b, #334155)',
              border: '1px solid #374151',
              borderRadius: '12px',
              padding: '2rem'
            }}>
              <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.3rem' }}>📊 Analysis Results</h3>

              {/* 3D Brain Visualization */}
              {results.visualization_url && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: '#d1d5db', marginBottom: '0.75rem' }}>🧠 3D Visualization</h4>
                  <iframe
                    src={`http://localhost:8000${results.visualization_url}`}
                    title="3D Brain Visualization"
                    style={{
                      width: '100%',
                      height: '600px',
                      border: 'none',
                      borderRadius: '8px',
                      background: '#1f2937'
                    }}
                  />
                </div>
              )}

              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ color: '#d1d5db', marginBottom: '0.75rem' }}>🎯 Key Metrics</h4>

                {/* Severity */}
                <div style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                  background: results.analysis.metrics.severity === 'High' || results.analysis.metrics.severity === 'Severe' ?
                    'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid ' + (results.analysis.metrics.severity === 'High' || results.analysis.metrics.severity === 'Severe' ?
                    'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)')
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Severity</span>
                    <span style={{
                      fontSize: '1.2rem',
                      fontWeight: 'bold',
                      textTransform: 'capitalize'
                    }}>
                      {results.analysis.metrics.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
                    Score: {results.analysis.metrics.severity_score}/4
                  </div>
                </div>

                {/* Volumes */}
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                  <div style={{
                    padding: '0.75rem',
                    background: 'rgba(6, 182, 212, 0.1)',
                    border: '1px solid rgba(6, 182, 212, 0.3)',
                    borderRadius: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#06b6d4' }}>Stroke Volume</span>
                      <span style={{ color: '#06b6d4', fontWeight: 'bold' }}>
                        {formatVolume(results.analysis.metrics.stroke_volume_mm3)}
                      </span>
                    </div>
                  </div>

                  <div style={{
                    padding: '0.75rem',
                    background: 'rgba(147, 197, 253, 0.1)',
                    border: '1px solid rgba(147, 197, 253, 0.3)',
                    borderRadius: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#93c5fd' }}>Brain Percentage</span>
                      <span style={{ color: '#93c5fd', fontWeight: 'bold' }}>
                        {(results.analysis.metrics.brain_percentage || 0).toFixed(3)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Explanation */}
              {results.analysis.ai_explanation && (
                <div style={{ marginBottom: '1.5rem' }}>

                  <h4 style={{ color: '#d1d5db', marginBottom: '0.75rem' }}>🤖 AI Analysis</h4>
                  <div style={{
                    padding: '1rem',
                    background: '#374151',
                    borderRadius: '6px',
                    fontSize: '0.9rem',
                    lineHeight: '1.5'
                  }}>
                    {results.analysis.ai_explanation.explanation}
                  </div>
                  <div style={{
                    marginTop: '0.5rem',
                    fontSize: '0.8rem',
                    color: '#9ca3af'
                  }}>
                    Confidence: {(results.analysis.ai_explanation.confidence * 100).toFixed(0)}%
                    • Model: {results.analysis.ai_explanation.model}
                  </div>
                </div>
              )}


              {/* Most Affected Slices */}
              {results.analysis.most_affected_slices && results.analysis.most_affected_slices.length > 0 && (
                <div>
                  <h4 style={{ color: '#d1d5db', marginBottom: '0.75rem' }}>📋 Most Affected Slices</h4>
                  <SliceGallery
                    slices={results.analysis.most_affected_slices.slice(0, 6).map(s => ({
                      ...s,
                      axis: 'axial'
                    }))}
                    fileId={processingState.fileId || ''}
                  />
                </div>
              )}
            </div>
          )}


        </div>

        {/* Footer */}
        <footer style={{
          textAlign: 'center',
          marginTop: '3rem',
          padding: '2rem',
          borderTop: '1px solid #374151',
          color: '#6b7280'
        }}>
          <p><strong>NeuroFlash v2.0</strong> - Advanced Brain Damage Segmentation 🧠✨</p>
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: '6px',
            fontSize: '0.8rem'
          }}>
            <strong>⚠️ Medical Disclaimer:</strong> Research and educational use only.
            Consult medical professionals for clinical decisions.
          </div>
        </footer>
      </main>
    </div>
  );
}

export default App;


