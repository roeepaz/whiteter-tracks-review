import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import roeeSong from '../assets/roeeSong.mp3';
import '../styles/logIn.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hasStartedRef = useRef(false); // כדי לא להפעיל שוב במקרה של לחיצה נוספת
  const navigate = useNavigate();

  useEffect(() => {
    audioRef.current = new Audio(roeeSong);
    audioRef.current.loop = true;

    const handleFirstClick = () => {
      if (!hasStartedRef.current && audioRef.current) {
        audioRef.current.play().then(() => {
          setIsPlaying(true);
          hasStartedRef.current = true;
        }).catch((err) => {
          console.warn('Playback failed:', err);
        });
      }
    };

    window.addEventListener('click', handleFirstClick);

    return () => {
      window.removeEventListener('click', handleFirstClick);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    };
  }, []);

  const toggleMusic = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch((err) => {
        console.warn('Playback failed:', err);
      });
    }
  };

  const handleLogin = () => {
    const adminArr = ['123', '123'];
    if (username === adminArr[0] && password === adminArr[1]) {
      sessionStorage.setItem('role', 'admin');
      navigate('/event-page');
    } else {
      alert('wrong user name or password. Please try again.');
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button onClick={handleLogin}>Login</button>

      <button onClick={toggleMusic} style={{ marginTop: '15px' }}>
        {isPlaying ? '🔇 השתק מוזיקה' : '🔊 הפעל מוזיקה'}
      </button>
    </div>
  );
};

export default Login;
