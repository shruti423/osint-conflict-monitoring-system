import { useState } from "react";
import { useNavigate } from "react-router-dom";

const LoginGate = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleConnect = () => {
    setLoading(true);
    setTimeout(() => navigate("/dashboard"), 1000);
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background animate-flicker">
      <div className="text-center space-y-6">
        <h1 className="text-3xl md:text-5xl font-bold text-foreground text-glow tracking-widest">
          OSINT CONFLICT MONITORING
        </h1>
        <p className="text-sm md:text-base text-muted-foreground tracking-wider">
          [SYSTEM STATUS: STANDBY — ACCESS SECURED LAYER]
        </p>

        {loading ? (
          <div className="mt-12 text-amber text-glow-amber text-xl tracking-widest animate-pulse">
            DECRYPTING...
          </div>
        ) : (
          <button
            onClick={handleConnect}
            className="mt-12 px-10 py-4 border-2 border-amber bg-transparent text-amber text-glow-amber font-bold tracking-widest text-lg rounded-none transition-all duration-150 hover:bg-amber hover:text-background active:scale-95"
          >
            [ INITIATE CONNECTION ]
          </button>
        )}

      </div>
    </div>
  );
};

export default LoginGate;
