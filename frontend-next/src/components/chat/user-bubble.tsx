interface UserBubbleProps {
  content: string;
}

export default function UserBubble({ content }: UserBubbleProps) {
  return (
    <div className="flex items-start justify-end gap-2">
      <div className="max-w-[75%] rounded-2xl rounded-br-sm bg-blue-600 px-4 py-2.5 text-sm text-white">
        {content}
      </div>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-lg" title="You">
        🧑
      </div>
    </div>
  );
}
