import { create } from 'zustand'
interface SettingsState { baseUrl: string; token: string; setBaseUrl: (v:string)=>void; setToken: (v:string)=>void; }
export const useSettingsStore = create<SettingsState>((set)=>({
  baseUrl: '', token: '',
  setBaseUrl: (v)=>set({baseUrl:v}), setToken: (v)=>set({token:v}),
}))
