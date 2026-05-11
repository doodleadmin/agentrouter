import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

function BaseIcon(props: IconProps) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props} />;
}

export const GridIcon = (props: IconProps) => <BaseIcon {...props}><rect x="3" y="3" width="8" height="8" rx="2" /><rect x="13" y="3" width="8" height="8" rx="2" /><rect x="3" y="13" width="8" height="8" rx="2" /><rect x="13" y="13" width="8" height="8" rx="2" /></BaseIcon>;
export const TeamIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="9" cy="9" r="3" /><circle cx="17" cy="10" r="2.5" /><path d="M3.5 19c0-2.2 2.5-4 5.5-4s5.5 1.8 5.5 4" /><path d="M14.5 18.5c.4-1.6 2-2.8 4-2.8 1 0 2 .3 2.7.9" /></BaseIcon>;
export const ChatIcon = (props: IconProps) => <BaseIcon {...props}><path d="M4 5h16v11H8l-4 4V5Z" /></BaseIcon>;
export const ShieldIcon = (props: IconProps) => <BaseIcon {...props}><path d="M12 3 5 6v6c0 4.2 2.7 7.4 7 9 4.3-1.6 7-4.8 7-9V6l-7-3Z" /><path d="m9.5 12 1.8 1.8 3.4-3.6" /></BaseIcon>;
export const HomeIcon = (props: IconProps) => <BaseIcon {...props}><path d="m3 11 9-7 9 7" /><path d="M6 10v10h12V10" /></BaseIcon>;
export const FolderIcon = (props: IconProps) => <BaseIcon {...props}><path d="M3 6h6l2 2h10v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Z" /></BaseIcon>;
export const RobotIcon = (props: IconProps) => <BaseIcon {...props}><rect x="5" y="7" width="14" height="12" rx="3" /><path d="M12 3v3" /><circle cx="9" cy="12" r="1" /><circle cx="15" cy="12" r="1" /><path d="M9 16h6" /></BaseIcon>;
export const TaskIcon = (props: IconProps) => <BaseIcon {...props}><rect x="4" y="4" width="16" height="16" rx="3" /><path d="m8 12 2.2 2.2L16 8.5" /></BaseIcon>;
export const MoreIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="6" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="18" cy="12" r="1.5" /></BaseIcon>;
export const CodeIcon = (props: IconProps) => <BaseIcon {...props}><path d="m9 8-4 4 4 4" /><path d="m15 8 4 4-4 4" /></BaseIcon>;
export const CloudIcon = (props: IconProps) => <BaseIcon {...props}><path d="M7 18a4 4 0 1 1 .7-7.9A5.5 5.5 0 0 1 18.6 12H19a3 3 0 1 1 0 6H7Z" /></BaseIcon>;
export const PackageIcon = (props: IconProps) => <BaseIcon {...props}><path d="m12 3 8 4.5-8 4.5-8-4.5L12 3Z" /><path d="M4 7.5V16l8 5 8-5V7.5" /><path d="M12 12v9" /></BaseIcon>;
export const TargetIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="1.5" /></BaseIcon>;
export const PaletteIcon = (props: IconProps) => <BaseIcon {...props}><path d="M12 4a8 8 0 1 0 0 16h1a2 2 0 0 0 0-4h-1a2 2 0 0 1 0-4h2a4 4 0 0 0 0-8h-2Z" /><circle cx="7.5" cy="10" r="1" /><circle cx="10" cy="7.5" r="1" /></BaseIcon>;
export const CogIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="12" cy="12" r="3" /><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a7.2 7.2 0 0 0-1.7-1l-.3-2.5h-4l-.3 2.5a7.2 7.2 0 0 0-1.7 1l-2.4-1-2 3.5 2 1.5a7 7 0 0 0 0 2l-2 1.5 2 3.5 2.4-1a7.2 7.2 0 0 0 1.7 1l.3 2.5h4l.3-2.5a7.2 7.2 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5c.1-.3.1-.6.1-1Z" /></BaseIcon>;
export const WrenchIcon = (props: IconProps) => <BaseIcon {...props}><path d="M14 6a4 4 0 0 0 4.7 4.7l-7.6 7.6a2 2 0 0 1-2.8-2.8l7.6-7.6A4 4 0 0 0 14 6Z" /></BaseIcon>;
export const FlaskIcon = (props: IconProps) => <BaseIcon {...props}><path d="M10 3v5l-5 8a3 3 0 0 0 2.5 4.5h9A3 3 0 0 0 19 16l-5-8V3" /><path d="M8 14h8" /></BaseIcon>;
export const SparklesIcon = (props: IconProps) => <BaseIcon {...props}><path d="m12 3 1.3 3.3L16.5 7.5l-3.2 1.2L12 12l-1.3-3.3L7.5 7.5l3.2-1.2L12 3Z" /><path d="m18 13 .7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7.7-1.8Z" /><path d="m6 13 .7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7.7-1.8Z" /></BaseIcon>;
export const ClipboardIcon = (props: IconProps) => <BaseIcon {...props}><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4.5h6" /><path d="M9 9h6M9 13h6M9 17h4" /></BaseIcon>;
export const SearchIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="11" cy="11" r="6" /><path d="m20 20-4.2-4.2" /></BaseIcon>;
export const DatabaseIcon = (props: IconProps) => <BaseIcon {...props}><ellipse cx="12" cy="6" rx="7" ry="3" /><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" /><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" /></BaseIcon>;
export const CheckCircleIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.2 2.2 4.6-4.6" /></BaseIcon>;
export const XCircleIcon = (props: IconProps) => <BaseIcon {...props}><circle cx="12" cy="12" r="9" /><path d="m9 9 6 6M15 9l-6 6" /></BaseIcon>;
