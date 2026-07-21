'use client';

interface PulseLineProps {
  className?: string;
  height?: number;
}

export default function PulseLine({ className = '', height = 32 }: PulseLineProps) {
  return (
    <svg
      className={`pulseLine ${className}`}
      viewBox="0 0 200 32"
      height={height}
      aria-hidden="true"
      role="presentation"
    >
      <polyline
        className="pulseLinePath"
        points="0,16 30,16 38,8 46,24 54,16 200,16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
