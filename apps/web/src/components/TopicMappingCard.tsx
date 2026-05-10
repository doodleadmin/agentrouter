import type { TelegramTopicRead } from '../types';
import { TOPIC_KIND_LABELS, TOPIC_KIND_DESCRIPTIONS } from '../types';
import { StatusPill } from './StatusPill';

const kindTone: Record<string, 'green' | 'blue' | 'orange' | 'gray'> = {
  general: 'blue',
  agent: 'green',
  approvals: 'orange',
  system_logs: 'gray',
  task: 'blue',
};

interface TopicMappingCardProps {
  topic: TelegramTopicRead;
}

export function TopicMappingCard({ topic }: TopicMappingCardProps) {
  const tone = kindTone[topic.kind] ?? 'gray';
  const label = TOPIC_KIND_LABELS[topic.kind as keyof typeof TOPIC_KIND_LABELS] ?? topic.kind;
  const description = TOPIC_KIND_DESCRIPTIONS[topic.kind as keyof typeof TOPIC_KIND_DESCRIPTIONS] ?? '';

  return (
    <article className="card">
      <div className="row-between">
        <strong>{topic.title}</strong>
        <StatusPill label={label} tone={tone} />
      </div>
      <p style={{ fontSize: '0.85rem', color: '#6b7280', margin: '4px 0' }}>{description}</p>
      <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>
        <div>chat_id: {topic.chat_id}</div>
        <div>thread: {topic.message_thread_id}</div>
        {topic.agent_id && <div>agent: {topic.agent_id}</div>}
        {!topic.is_active && <div style={{ color: '#dc2626' }}>inactive</div>}
      </div>
    </article>
  );
}
