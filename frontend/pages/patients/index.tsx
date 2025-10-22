import Head from 'next/head';
import Link from 'next/link';
import { useState, useEffect } from 'react';

interface Patient {
  id: number;
  name: string;
  age: number;
  gender: string;
  contact: string | null;
}

const PatientsPage = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    contact: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBase}/patients`);
      if (!response.ok) {
        throw new Error('Failed to fetch patients');
      }
      const data = await response.json();
      setPatients(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
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

      // Reset form and refresh list
      setFormData({ name: '', age: '', gender: '', contact: '' });
      await fetchPatients();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <Head>
        <title>Patients - LIMS</title>
      </Head>
      <main>
        <h1>Patient Management</h1>
        <p>
          <Link href="/">← Back to Dashboard</Link>
        </p>

        {error && (
          <div style={{ 
            padding: '1rem', 
            backgroundColor: '#fee', 
            border: '1px solid #fcc',
            borderRadius: '4px',
            marginBottom: '1rem'
          }}>
            Error: {error}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem' }}>
          {/* Patient List */}
          <div>
            <h2>Patient List</h2>
            {loading ? (
              <p>Loading patients...</p>
            ) : patients.length === 0 ? (
              <p>No patients found. Create one using the form.</p>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #ddd' }}>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>ID</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Name</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Age</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Gender</th>
                    <th style={{ padding: '0.5rem', textAlign: 'left' }}>Contact</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((patient) => (
                    <tr key={patient.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '0.5rem' }}>{patient.id}</td>
                      <td style={{ padding: '0.5rem' }}>{patient.name}</td>
                      <td style={{ padding: '0.5rem' }}>{patient.age}</td>
                      <td style={{ padding: '0.5rem' }}>{patient.gender}</td>
                      <td style={{ padding: '0.5rem' }}>{patient.contact || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Create Patient Form */}
          <div>
            <h2>Create New Patient</h2>
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
                  style={{ width: '100%', padding: '0.5rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}
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
                  style={{ width: '100%', padding: '0.5rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}
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
                  style={{ width: '100%', padding: '0.5rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}
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
                  style={{ width: '100%', padding: '0.5rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}
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
                {submitting ? 'Creating...' : 'Create Patient'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};

export default PatientsPage;
