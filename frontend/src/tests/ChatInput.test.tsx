import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInput } from '../components/chat/ChatInput';

describe('ChatInput', () => {
  it('renders textarea and send button', () => {
    render(<ChatInput onSend={vi.fn()} />);
    expect(screen.getByPlaceholderText(/输入消息/)).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('calls onSend on Enter key', async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/输入消息/);
    await userEvent.type(textarea, 'Hello{Enter}');
    expect(onSend).toHaveBeenCalledWith('Hello');
  });

  it('does not call onSend on Shift+Enter', async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/输入消息/);
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
  });

  it('disables button when input is empty', () => {
    render(<ChatInput onSend={vi.fn()} />);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
  });

  it('disables input when disabled prop is true', () => {
    render(<ChatInput onSend={vi.fn()} disabled={true} />);
    const textarea = screen.getByPlaceholderText(/输入消息/);
    expect(textarea).toBeDisabled();
  });

  it('clears input after sending', async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/输入消息/);
    await userEvent.type(textarea, 'Test message{Enter}');
    expect(textarea).toHaveValue('');
  });
});
