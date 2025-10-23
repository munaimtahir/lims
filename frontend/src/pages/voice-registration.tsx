import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import VoiceInput from '../components/VoiceInput';

interface ConfidenceLevel {
  value: number;
  label: string;
  color: string;
}

const VoiceRegistrationPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    contact: '',
  });
  const [mapping, setMapping] = useState<any>(null);
  const [transcript, setTranscript] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const getConfidenceLevel = (confidence: number): ConfidenceLevel => {
    if (confidence >= 0.9) {
      return { value: confidence, label: 'Auto-accepted ✓', color: '#28a745' };
    } else if (confidence >= 0.6) {
      return { value: confidence, label: 'Confirm?', color: '#ffc107' };
    } else {
      return { value: confidence, label: 'Manual Entry', color: '#dc3545' };
    }
  };

  const handleTranscriptReceived = (text: string) => {
    setTranscript(text);
  };

  const handleMappingReceived = (data: any) => {
    setMapping(data);
    
    // Auto-fill form with extracted fields
    if (data.fields) {
      setFormData({
        name: data.fields.name || '',
        age: data.fields.age?.toString() || '',
        gender: data.fields.gender || '',
        contact: data.fields.contact || '',
      });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccess(false);
    
    try {
      const response = await fetch(`${apiBase}/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          age: parseInt(formData.age, 10),
          gender: formData.gender,
          contact: formData.contact || null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create patient');
      }

      // Reset form and show success
      setFormData({ name: '', age: '', gender: '', contact: '' });
      setMapping(null);
      setTranscript('');
      setSuccess(true);
      
      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
      <Head>
        <title>Voice Registration - LIMS</title>
      </Head>
      <main>
        <h1>Voice-Enabled Patient Registration</h1>
        <p>
          <Link href="/">← Back to Dashboard</Link>
        </p>

        {success && (
          <div style={{ 
            padding: '1rem', 
            backgroundColor: '#d4edda', 
            border: '1px solid #c3e6cb',
            borderRadius: '4px',
            marginBottom: '1rem',
            color: '#155724'
          }}>
            ✓ Patient registered successfully!
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem' }}>
          {/* Voice Input Panel */}
          <div>
            <VoiceInput
              onTranscriptReceived={handleTranscriptReceived}
              onMappingReceived={handleMappingReceived}
              language="en-US"
            />

            {mapping && (
              <div style={{ marginTop: '1rem' }}>
                <h3>Confidence Scores</h3>
                {Object.keys(mapping.confidences || {}).map((field) => {
                  const conf = mapping.confidences[field];
                  const level = getConfidenceLevel(conf);
                  
                  return (
                    <div
                      key={field}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.5rem',
                        marginBottom: '0.5rem',
                        backgroundColor: '#fff',
                        border: '1px solid #ddd',
                        borderRadius: '4px'
                      }}
                    >
                      <span style={{ fontWeight: 'bold', textTransform: 'capitalize' }}>
                        {field}:
                      </span>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          borderRadius: '12px',
                          fontSize: '0.85rem',
                          fontWeight: 'bold',
                          backgroundColor: level.color,
                          color: 'white'
                        }}
                      >
                        {level.label} ({(conf * 100).toFixed(0)}%)
                      </span>
                    </div>
                  );
                })}
                
                <div style={{ 
                  marginTop: '1rem', 
                  padding: '0.75rem', 
                  backgroundColor: '#e7f3ff',
                  border: '1px solid #b3d9ff',
                  borderRadius: '4px'
                }}>
                  <strong>Overall Confidence:</strong> {(mapping.overall_confidence * 100).toFixed(0)}%
                  {mapping.requires_confirmation && (
                    <p style={{ marginTop: '0.5rem', marginBottom: 0, fontSize: '0.9rem' }}>
                      ⚠️ Please confirm the extracted fields before submitting.
                    </p>
                  )}
                  {mapping.requires_manual && (
                    <p style={{ marginTop: '0.5rem', marginBottom: 0, fontSize: '0.9rem' }}>
                      ⚠️ Low confidence - please review and correct manually.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Patient Form */}
          <div>
            <h2>Patient Information</h2>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label htmlFor="name" style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>
                  Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    fontSize: '1rem', 
                    border: '1px solid #ccc', 
                    borderRadius: '4px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label htmlFor="age" style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>
                  Age *
                </label>
                <input
                  type="number"
                  id="age"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  required
                  min="0"
                  max="150"
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    fontSize: '1rem', 
                    border: '1px solid #ccc', 
                    borderRadius: '4px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label htmlFor="gender" style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>
                  Gender *
                </label>
                <select
                  id="gender"
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  required
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    fontSize: '1rem', 
                    border: '1px solid #ccc', 
                    borderRadius: '4px',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value="">Select gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label htmlFor="contact" style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 'bold' }}>
                  Contact
                </label>
                <input
                  type="text"
                  id="contact"
                  name="contact"
                  value={formData.contact}
                  onChange={handleChange}
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    fontSize: '1rem', 
                    border: '1px solid #ccc', 
                    borderRadius: '4px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                style={{
                  padding: '0.75rem 1.5rem',
                  fontSize: '1rem',
                  fontWeight: 'bold',
                  color: 'white',
                  backgroundColor: submitting ? '#999' : '#007bff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                }}
              >
                {submitting ? 'Registering...' : 'Register Patient'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};

export default VoiceRegistrationPage;
