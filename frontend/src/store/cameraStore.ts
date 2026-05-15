import { create } from 'zustand';
import { Camera, Detection, CameraStatus } from '../types';

interface CameraStore {
  cameras: Camera[];
  statuses: CameraStatus[];
  selectedCamera: string | null;
  setCameras: (cameras: Camera[]) => void;
  setStatuses: (statuses: CameraStatus[]) => void;
  selectCamera: (id: string | null) => void;
}

export const useCameraStore = create<CameraStore>((set) => ({
  cameras: [],
  statuses: [],
  selectedCamera: null,
  setCameras: (cameras) => set({ cameras }),
  setStatuses: (statuses) => set({ statuses }),
  selectCamera: (id) => set({ selectedCamera: id }),
}));
