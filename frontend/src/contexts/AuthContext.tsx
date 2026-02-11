import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import type { User, AuthState, LoginRequest, Branch } from '../types';
import { authApi } from '../api/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setCurrentBranch: (branch: any) => void;
}


const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isAuthenticated: false,
  isLoading: true,
  currentBranch: null,
};

type AuthAction =
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; accessToken: string; refreshToken: string; currentBranch: Branch | null } }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User }
  | { type: 'SET_CURRENT_BRANCH'; payload: Branch };

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
        currentBranch: action.payload.currentBranch,
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
    case 'SET_CURRENT_BRANCH':
      return {
        ...state,
        currentBranch: action.payload,
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
        const user = response.data;
        let branch: Branch | null = null;

        // Restore branch from localStorage or pick default
        const savedBranchCode = localStorage.getItem('currentBranchCode');
        if (savedBranchCode && user.branch_memberships?.length > 0) {
          const matched = user.branch_memberships.find(m => m.branch.code === savedBranchCode);
          if (matched) branch = matched.branch;
        }

        // Fallback to first branch if no match or no saved branch
        if (!branch && user.branch_memberships?.length > 0) {
          branch = user.branch_memberships[0].branch;
        }

        // Save fresh user
        localStorage.setItem('user', JSON.stringify(user));
        if (branch) localStorage.setItem('currentBranchCode', branch.code);

        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user,
            accessToken,
            refreshToken: localStorage.getItem('refreshToken') || '',
            currentBranch: branch,
          },
        });
      } else {
        dispatch({ type: 'LOGOUT' });
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        localStorage.removeItem('currentBranchCode');
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

        // Determine default branch
        let branch: Branch | null = null;
        if (user.branch_memberships?.length > 0) {
          branch = user.branch_memberships[0].branch;
        }

        // Store tokens and user in localStorage
        localStorage.setItem('accessToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        localStorage.setItem('user', JSON.stringify(user));
        if (branch) localStorage.setItem('currentBranchCode', branch.code);

        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: {
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            currentBranch: branch,
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
      localStorage.removeItem('currentBranchCode');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    checkAuth,
    setCurrentBranch: (branch: Branch) => {
      localStorage.setItem('currentBranchCode', branch.code);
      dispatch({ type: 'SET_CURRENT_BRANCH', payload: branch });
    },
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
