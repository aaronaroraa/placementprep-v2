import { create } from 'zustand'

export const useStore = create((set, get) => ({
  user: null,
  dashboard: null,
  setUser: user => set({ user }),
  setDashboard: dashboard => set({ dashboard }),
  clearUser: () => set({ user: null, dashboard: null }),
  updateTask: (taskId, updates) => set(s => ({
    dashboard: s.dashboard ? {
      ...s.dashboard,
      today_tasks: s.dashboard.today_tasks.map(t => t.id === taskId ? { ...t, ...updates } : t),
    } : s.dashboard,
  })),
}))
