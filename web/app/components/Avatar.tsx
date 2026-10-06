const COLORS = [
  "bg-red-100 text-red-700",
  "bg-orange-100 text-orange-700",
  "bg-amber-100 text-amber-700",
  "bg-green-100 text-green-700",
  "bg-teal-100 text-teal-700",
  "bg-blue-100 text-blue-700",
  "bg-indigo-100 text-indigo-700",
  "bg-purple-100 text-purple-700",
  "bg-pink-100 text-pink-700",
];

function colorForUsername(username: string): string {
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }
  return COLORS[Math.abs(hash) % COLORS.length];
}

export default function Avatar({
  username,
  size = "md",
}: {
  username: string;
  size?: "sm" | "md" | "lg";
}) {
  const initials = username.slice(0, 2).toUpperCase();
  const colorClasses = colorForUsername(username);

  const sizeClasses = {
    sm: "h-8 w-8 text-xs",
    md: "h-12 w-12 text-base",
    lg: "h-20 w-20 text-2xl",
  }[size];

  return (
    <div
      className={`flex flex-shrink-0 items-center justify-center rounded-full font-medium ${colorClasses} ${sizeClasses}`}
    >
      {initials}
    </div>
  );
}
