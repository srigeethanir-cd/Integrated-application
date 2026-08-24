import React from 'react';

export default function LogoutModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white p-6 rounded-xl max-w-xs w-full text-center space-y-4">
        <h3 className="text-lg font-bold text-slate-900">Confirm Logout</h3>
        <p className="text-xs text-slate-500">You will need to sign in again to access your tasks.</p>
        <div className="flex justify-center gap-2">
          <button onClick={onClose} className="px-4 py-2 border rounded text-xs">Cancel</button>
          <button onClick={() => window.location.href = '/login'} className="px-4 py-2 bg-red-600 text-white rounded font-bold text-xs">Logout</button>
        </div>
      </div>
    </div>
  );
}
