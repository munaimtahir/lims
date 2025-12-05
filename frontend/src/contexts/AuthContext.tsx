import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import type { User, AuthState, LoginRequest } from '../types';
import { authApi } from '../api/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
};

type AuthAction =
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; accessToken: string; refreshToken: string } }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
        isAuthenticated: true,
        isLoading: false,
      };
    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    default:
      return state;
  }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  /**
   * Check if user is authenticated on app load
   */
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    const accessToken = localStorage.getItem('accessToken');
    const userStr = localStorage.getItem('user');

    if (!accessToken || !userStr) {
      dispatch({ type: 'LOGOUT' });
      return;
    }

    try {
      // Verify token is still valid by fetching current user
      const response = await authApi.me();
      
      if (response.success && response.data) {
        localStorage.setItem('user', JSON.stringify(response.data));
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user: response.data,
            accessToken,
            refreshToken: localStorage.getItem('refreshToken') || '',
          },
        });
      } else {
        dispatch({ type: 'LOGOUT' });
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      dispatch({ type: 'LOGOUT' });
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  };

  const login = async (credentials: LoginRequest) => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await authApi.login(credentials);

      if (response.success) {
        const { user, access_token, refresh_token } = response.data;

        // Store tokens and user in localStorage
        localStorage.setItem('accessToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        localStorage.setItem('user', JSON.stringify(user));

        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
          },
        });
      } else {
        throw new Error(response.message || 'Login failed');
      }
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    
    try {
      await authApi.logout(refreshToken || undefined);
    } finally {
      // Clear local storage and state regardless of API result
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
