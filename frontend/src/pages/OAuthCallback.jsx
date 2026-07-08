import { useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { TOKEN_KEYS } from '../utils/constants';
import Loading from '../components/Common/Loading';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { fetchUser } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const error = searchParams.get('error');

    if (error) {
      navigate(`/login?error=${error}`, { replace: true });
      return;
    }

    if (accessToken) {
      localStorage.setItem(TOKEN_KEYS.ACCESS, accessToken);
      if (refreshToken) {
        localStorage.setItem(TOKEN_KEYS.REFRESH, refreshToken);
      }

      // Fetch user profile and redirect to dashboard
      fetchUser().then(() => {
        navigate('/dashboard', { replace: true });
      }).catch(() => {
        navigate('/login?error=profile_fetch_failed', { replace: true });
      });
    } else {
      navigate('/login?error=no_token', { replace: true });
    }
  }, [searchParams, navigate, fetchUser]);

  return <Loading fullScreen />;
}
