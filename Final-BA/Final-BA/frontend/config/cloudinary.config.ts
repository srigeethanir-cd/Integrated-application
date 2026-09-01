// Cloudinary Configuration — used internally by the app only
// These values are NEVER shown in the UI

export const CLOUDINARY_CONFIG = {
  cloudName: 'yw4xqfan',
  apiKey: '459677175763116',
  apiSecret: 'MjvCEtJF5mgWl-NbfQAVSI4Z7b0',
  folder: 'logos',
  allowedFormats: ['jpg', 'jpeg', 'png'],
  maxFileSizeMB: 2,
};

export type CloudinaryConfig = typeof CLOUDINARY_CONFIG;
