import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { systemSettingsApi } from '../api/services';
import type { SystemSettings } from '../types';

interface BrandingContextValue {
  branding: SystemSettings | null;
  isLoading: boolean;
  error: string | null;
  refreshBranding: () => Promise<void>;
}

const BrandingContext = createContext<BrandingContextValue | undefined>(undefined);

export function BrandingProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBranding = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await systemSettingsApi.get();
      setBranding(response.data);
    } catch (err) {
      console.error('Failed to fetch branding settings:', err);
      setError('Failed to load branding settings');
      // Set default branding on error
      setBranding({
        id: 1,
        lab_name: 'LIMS',
        currency: 'PKR',
        tax_rate: '0.00',
        email_port: 587,
        email_use_tls: true,
        email_use_ssl: false,
        backup_enabled: false,
        backup_frequency: 'daily',
        updated_at: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBranding();
  }, []);

  const refreshBranding = async () => {
    await fetchBranding();
  };

  return (
    <BrandingContext.Provider value={{ branding, isLoading, error, refreshBranding }}>
      {children}
    </BrandingContext.Provider>
  );
}

export function useBranding() {
  const context = useContext(BrandingContext);
  if (context === undefined) {
    throw new Error('useBranding must be used within a BrandingProvider');
  }
  return context;
}
