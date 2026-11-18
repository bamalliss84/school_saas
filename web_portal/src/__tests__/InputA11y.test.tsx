import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Input } from '../components/ui/Input';

describe('Input accessibility', () => {
  it('uses the placeholder as the accessible name when there is no visible label', () => {
    render(<Input placeholder="بحث بالاسم" />);
    expect(screen.getByRole('textbox', { name: 'بحث بالاسم' })).toBeInTheDocument();
  });

  it('keeps the visible label as the name and does not duplicate it', () => {
    render(<Input label="الاسم الكامل" placeholder="مثال: أحمد" />);
    const field = screen.getByRole('textbox', { name: 'الاسم الكامل' });
    expect(field).not.toHaveAttribute('aria-label');
  });

  it('an explicit aria-label wins over the placeholder', () => {
    render(<Input placeholder="..." aria-label="بحث في الطلاب" />);
    expect(screen.getByRole('textbox', { name: 'بحث في الطلاب' })).toBeInTheDocument();
  });

  it('links the error message to the field and marks it invalid', () => {
    render(<Input label="البريد" error="البريد غير صحيح" />);
    const field = screen.getByRole('textbox', { name: 'البريد' });
    expect(field).toHaveAttribute('aria-invalid', 'true');
    expect(field).toHaveAccessibleDescription('البريد غير صحيح');
    expect(screen.getByRole('alert')).toHaveTextContent('البريد غير صحيح');
  });

  it('links the hint when there is no error', () => {
    render(<Input label="كلمة المرور" hint="8 أحرف على الأقل" />);
    const field = screen.getByRole('textbox', { name: 'كلمة المرور' });
    expect(field).toHaveAccessibleDescription('8 أحرف على الأقل');
    expect(field).not.toHaveAttribute('aria-invalid');
  });
});
