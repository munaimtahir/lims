import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { coreApi } from '../../api/services';
import type { Branch, CollectionCenter } from '../../types';
import styles from './BranchesAndCentersPage.module.css';

const CAPABILITY_OPTIONS: Branch['capability_mode'][] = ['COLLECT_ONLY', 'COLLECT_AND_PROCESS', 'HQ_PROCESSING'];

export default function BranchesAndCentersPage() {
  const queryClient = useQueryClient();
  const [branchModal, setBranchModal] = useState<{ open: boolean; branch?: Branch | null }>({ open: false, branch: null });
  const [centerModal, setCenterModal] = useState<{ open: boolean; center?: CollectionCenter | null }>({ open: false, center: null });

  const { data: branches = [], isLoading: loadingBranches } = useQuery({
    queryKey: ['core-branches'],
    queryFn: () => coreApi.listBranches(),
  });

  const { data: centers = [], isLoading: loadingCenters } = useQuery({
    queryKey: ['core-collection-centers'],
    queryFn: () => coreApi.listCollectionCenters(),
  });

  const branchCreateMutation = useMutation({
    mutationFn: (data: Partial<Branch>) => coreApi.createBranch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['core-branches'] });
      setBranchModal({ open: false, branch: null });
      alert('Branch created.');
    },
    onError: (e: any) => alert(e?.response?.data?.detail || e?.message || 'Failed to create branch'),
  });

  const branchUpdateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Branch> }) => coreApi.updateBranch(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['core-branches'] });
      setBranchModal({ open: false, branch: null });
      alert('Branch updated.');
    },
    onError: (e: any) => alert(e?.response?.data?.detail || e?.message || 'Failed to update branch'),
  });

  const branchDeleteMutation = useMutation({
    mutationFn: (id: number) => coreApi.deleteBranch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['core-branches'] });
      setBranchModal({ open: false, branch: null });
      alert('Branch deleted.');
    },
    onError: (e: any) => alert(e?.response?.data?.detail || e?.message || 'Failed to delete branch'),
  });

  const centerCreateMutation = useMutation({
    mutationFn: (data: Partial<CollectionCenter>) => coreApi.createCollectionCenter(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['core-collection-centers'] });
      setCenterModal({ open: false, center: null });
      alert('Collection center created.');
    },
    onError: (e: any) => alert(e?.response?.data?.detail || e?.message || 'Failed to create collection center'),
  });

  const centerUpdateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CollectionCenter> }) => coreApi.updateCollectionCenter(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['core-collection-centers'] });
      setCenterModal({ open: false, center: null });
      alert('Collection center updated.');
    },
    onError: (e: any) => alert(e?.response?.data?.detail || e?.message || 'Failed to update collection center'),
  });

  const centerDeleteMutation = useMutation({
    mutationFn: (id: number) => coreApi.deleteCollectionCenter(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['core-collection-centers'] });
      setCenterModal({ open: false, center: null });
      alert('Collection center deleted.');
    },
    onError: (e: any) => alert(e?.response?.data?.detail || e?.message || 'Failed to delete collection center'),
  });

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Branches &amp; Collection Centers</h1>
        <p className={styles.subtitle}>Add, edit, or remove branches and collection centers (admin).</p>
      </header>

      <section className={styles.section}>
        <h2>Branches</h2>
        <p className={styles.hint}>Branches are scoped to your tenant. Code must be 2 digits (00–99). Code 00 is HQ.</p>
        <div className={styles.toolbar}>
          <button type="button" className={styles.primaryButton} onClick={() => setBranchModal({ open: true, branch: null })}>
            Add Branch
          </button>
        </div>
        {loadingBranches ? <p>Loading branches…</p> : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Capability</th>
                <th>HQ</th>
                <th>Active</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {branches.map((b) => (
                <tr key={b.id}>
                  <td>{b.code}</td>
                  <td>{b.name}</td>
                  <td>{b.capability_mode?.replace(/_/g, ' ') ?? '—'}</td>
                  <td>{b.is_hq ? 'Yes' : '—'}</td>
                  <td>{b.is_active ? 'Yes' : 'No'}</td>
                  <td>
                    <button type="button" className={styles.smallButton} onClick={() => setBranchModal({ open: true, branch: b })}>Edit</button>
                    <button type="button" className={styles.smallButtonDanger} onClick={() => window.confirm('Delete this branch?') && branchDeleteMutation.mutate(b.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {branches.length === 0 && !loadingBranches && <p className={styles.empty}>No branches yet. Add one above.</p>}
      </section>

      <section className={styles.section}>
        <h2>Collection Centers</h2>
        <p className={styles.hint}>Collection centers are system-wide. Code must be 2 digits (00–99).</p>
        <div className={styles.toolbar}>
          <button type="button" className={styles.primaryButton} onClick={() => setCenterModal({ open: true, center: null })}>
            Add Collection Center
          </button>
        </div>
        {loadingCenters ? <p>Loading collection centers…</p> : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Active</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {centers.map((c) => (
                <tr key={c.id}>
                  <td>{c.code}</td>
                  <td>{c.name}</td>
                  <td>{c.is_active ? 'Yes' : 'No'}</td>
                  <td>
                    <button type="button" className={styles.smallButton} onClick={() => setCenterModal({ open: true, center: c })}>Edit</button>
                    <button type="button" className={styles.smallButtonDanger} onClick={() => window.confirm('Delete this collection center?') && centerDeleteMutation.mutate(c.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {centers.length === 0 && !loadingCenters && <p className={styles.empty}>No collection centers yet. Add one above.</p>}
      </section>

      {branchModal.open && (
        <BranchModal
          branch={branchModal.branch ?? undefined}
          onClose={() => setBranchModal({ open: false, branch: null })}
          onSave={(data) => {
            if (branchModal.branch?.id) {
              branchUpdateMutation.mutate({ id: branchModal.branch.id, data });
            } else {
              branchCreateMutation.mutate(data);
            }
          }}
          saving={branchCreateMutation.isPending || branchUpdateMutation.isPending}
        />
      )}

      {centerModal.open && (
        <CollectionCenterModal
          center={centerModal.center ?? undefined}
          onClose={() => setCenterModal({ open: false, center: null })}
          onSave={(data) => {
            if (centerModal.center?.id) {
              centerUpdateMutation.mutate({ id: centerModal.center.id, data });
            } else {
              centerCreateMutation.mutate(data);
            }
          }}
          saving={centerCreateMutation.isPending || centerUpdateMutation.isPending}
        />
      )}
    </div>
  );
}

function BranchModal({
  branch,
  onClose,
  onSave,
  saving,
}: {
  branch?: Branch | null;
  onClose: () => void;
  onSave: (data: Partial<Branch>) => void;
  saving: boolean;
}) {
  const [code, setCode] = useState(branch?.code ?? '');
  const [name, setName] = useState(branch?.name ?? '');
  const [address, setAddress] = useState(branch?.address ?? '');
  const [phone, setPhone] = useState(branch?.phone ?? '');
  const [capability_mode, setCapability_mode] = useState<Branch['capability_mode']>(branch?.capability_mode ?? 'COLLECT_ONLY');
  const [is_active, setIs_active] = useState(branch?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) {
      alert('Code and name are required.');
      return;
    }
    if (!/^\d{2}$/.test(code.trim())) {
      alert('Code must be exactly 2 digits (00–99).');
      return;
    }
    onSave({ code: code.trim(), name: name.trim(), address: address.trim() || undefined, phone: phone.trim() || undefined, capability_mode, is_active });
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <h3>{branch ? 'Edit Branch' : 'Add Branch'}</h3>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Code (2 digits) *</label>
            <input value={code} onChange={e => setCode(e.target.value)} placeholder="00" maxLength={2} disabled={!!branch?.id} />
          </div>
          <div className={styles.formGroup}>
            <label>Name *</label>
            <input value={name} onChange={e => setName(e.target.value)} required />
          </div>
          <div className={styles.formGroup}>
            <label>Address</label>
            <textarea value={address} onChange={e => setAddress(e.target.value)} rows={2} />
          </div>
          <div className={styles.formGroup}>
            <label>Phone</label>
            <input value={phone} onChange={e => setPhone(e.target.value)} />
          </div>
          <div className={styles.formGroup}>
            <label>Capability</label>
            <select value={capability_mode} onChange={e => setCapability_mode(e.target.value as Branch['capability_mode'])}>
              {CAPABILITY_OPTIONS.map(opt => (
                <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div className={styles.formGroup}>
            <label>
              <input type="checkbox" checked={is_active} onChange={e => setIs_active(e.target.checked)} />
              Active
            </label>
          </div>
          <div className={styles.modalActions}>
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CollectionCenterModal({
  center,
  onClose,
  onSave,
  saving,
}: {
  center?: CollectionCenter | null;
  onClose: () => void;
  onSave: (data: Partial<CollectionCenter>) => void;
  saving: boolean;
}) {
  const [code, setCode] = useState(center?.code ?? '');
  const [name, setName] = useState(center?.name ?? '');
  const [address, setAddress] = useState(center?.address ?? '');
  const [is_active, setIs_active] = useState(center?.is_active ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) {
      alert('Code and name are required.');
      return;
    }
    if (!/^\d{2}$/.test(code.trim())) {
      alert('Code must be exactly 2 digits (00–99).');
      return;
    }
    onSave({ code: code.trim(), name: name.trim(), address: address.trim() || undefined, is_active });
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <h3>{center ? 'Edit Collection Center' : 'Add Collection Center'}</h3>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>Code (2 digits) *</label>
            <input value={code} onChange={e => setCode(e.target.value)} placeholder="00" maxLength={2} disabled={!!center?.id} />
          </div>
          <div className={styles.formGroup}>
            <label>Name *</label>
            <input value={name} onChange={e => setName(e.target.value)} required />
          </div>
          <div className={styles.formGroup}>
            <label>Address</label>
            <textarea value={address} onChange={e => setAddress(e.target.value)} rows={2} />
          </div>
          <div className={styles.formGroup}>
            <label>
              <input type="checkbox" checked={is_active} onChange={e => setIs_active(e.target.checked)} />
              Active
            </label>
          </div>
          <div className={styles.modalActions}>
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
