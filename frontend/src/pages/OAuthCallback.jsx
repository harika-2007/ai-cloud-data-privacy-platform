import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { TOKEN_KEYS } from '../utils/constants';
import Loading from '../components/Common/Loading';

/**
 * OAuth Callback Page
 *
 * Receives JWT tokens from the backend after a successful Google OAuth
 * sign-in. Tokens are delivered via URL fragment (#) to prevent them
 * from being logged by nginx / reverse proxies or stored in browser history.
 *
 * Also handles error redirects via query params (?) for error cases.
 */
export default function OAuthCallback() {
  const navigate = useNavigate();
  const { fetchUser } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    // Parse tokens from URL fragment (#) — the secure delivery mechanism
    const hash = window.location.hash || '';
    const hashParams = new URLSearchParams(hash.replace(/^#/, ''));
    const accessToken = hashParams.get('access_token');
    const refreshToken = hashParams.get('refresh_token');

    // Parse errors from query params (?) — error delivery is not sensitive
    const searchParams = new URLSearchParams(window.location.search);
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

      // Clear the fragment from the URL without triggering a page reload
      window.location.hash = '';

      // Fetch user profile and redirect to dashboard
      fetchUser().then(() => {
        navigate('/dashboard', { replace: true });
      }).catch(() => {
        navigate('/login?error=profile_fetch_failed', { replace: true });
      });
    } else {
      navigate('/login?error=no_token', { replace: true });
    }
  }, [navigate, fetchUser]);

  return <Loading fullScreen />;
}
