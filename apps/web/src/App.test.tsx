import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from './App';

describe('development entry point', () => {
  it('identifies Arxen and the development-only state', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Arxen', level: 1 })).toBeVisible();
    expect(screen.getByText('Ambiente de desenvolvimento')).toBeVisible();
  });
});
