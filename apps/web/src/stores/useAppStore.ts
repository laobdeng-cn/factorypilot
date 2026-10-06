import { create } from 'zustand';

interface AppShellState {
  companyName: string;
  currentPlant: string;
  setCurrentPlant: (plant: string) => void;
}

export const useAppStore = create<AppShellState>((set) => ({
  companyName: '华南精密电子有限公司',
  currentPlant: '东莞制造基地',
  setCurrentPlant: (plant) => set({ currentPlant: plant }),
}));
