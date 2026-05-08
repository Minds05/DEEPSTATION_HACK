import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';

const Toast = ({ message, type }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl border backdrop-blur-md pointer-events-auto
      ${type === 'overdue' 
        ? 'bg-red-500/10 border-red-500/50 text-red-200' 
        : 'bg-emerald-500/10 border-emerald-500/50 text-emerald-200'}`}
    >
      {type === 'overdue' ? <AlertCircle size={20} className="text-red-400" /> : <CheckCircle size={20} className="text-emerald-400" />}
      <p className="font-medium text-sm">{message}</p>
    </div>
  );
};

export default Toast;
