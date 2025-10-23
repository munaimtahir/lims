import { useState, useEffect } from 'react';

interface VoiceInputProps {
  onTranscriptReceived: (transcript: string) => void;
  onMappingReceived: (mapping: any) => void;
  language?: string;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ 
  onTranscriptReceived, 
  onMappingReceived,
  language = 'en-US' 
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    // Check if Web Speech API is available
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      
      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = false;
        recognitionInstance.lang = language;

        recognitionInstance.onresult = (event: any) => {
          const transcriptText = event.results[0][0].transcript;
          setTranscript(transcriptText);
          onTranscriptReceived(transcriptText);
          
          // Send to backend for mapping
          mapTranscript(transcriptText);
        };

        recognitionInstance.onerror = (event: any) => {
          setError(`Error: ${event.error}`);
          setIsListening(false);
        };

        recognitionInstance.onend = () => {
          setIsListening(false);
        };

        setRecognition(recognitionInstance);
      } else {
        setError('Web Speech API not supported in this browser');
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  const mapTranscript = async (text: string) => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/voice/map`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: text,
          user: 'frontend_user',
          action_type: 'registration'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to map transcript');
      }

      const data = await response.json();
      onMappingReceived(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to map transcript');
    }
  };

  const startListening = () => {
    if (recognition) {
      setError(null);
      setTranscript('');
      setIsListening(true);
      recognition.start();
    }
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  };

  return (
    <div style={{ 
      padding: '1rem', 
      border: '1px solid #ddd', 
      borderRadius: '8px',
      backgroundColor: '#f9f9f9'
    }}>
      <h3 style={{ marginTop: 0 }}>Voice Input</h3>
      
      {error && (
        <div style={{ 
          padding: '0.5rem', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          marginBottom: '1rem',
          fontSize: '0.9rem'
        }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '1rem' }}>
        <button
          onClick={isListening ? stopListening : startListening}
          disabled={!recognition}
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            fontWeight: 'bold',
            color: 'white',
            backgroundColor: isListening ? '#dc3545' : '#28a745',
            border: 'none',
            borderRadius: '4px',
            cursor: recognition ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>
            {isListening ? '⏹' : '🎤'}
          </span>
          {isListening ? 'Stop Recording' : 'Start Voice Input'}
        </button>
      </div>

      {transcript && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#fff',
          border: '1px solid #ccc',
          borderRadius: '4px',
          marginTop: '1rem'
        }}>
          <strong>Transcript:</strong>
          <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>{transcript}</p>
        </div>
      )}
    </div>
  );
};

export default VoiceInput;
