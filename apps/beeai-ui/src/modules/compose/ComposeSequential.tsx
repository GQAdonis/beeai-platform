/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Suspense } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import { ComposeView } from './components/ComposeView';
import type { SequentialFormValues } from './contexts/compose-context';
import { ComposeProvider } from './contexts/ComposeProvider';

export function ComposeSequential() {
  const formReturn = useForm<SequentialFormValues>({
    mode: 'onChange',
    defaultValues: { steps: [] },
  });

  return (
    <Suspense>
      <FormProvider {...formReturn}>
        <ComposeProvider>
          <ComposeView />
        </ComposeProvider>
      </FormProvider>
    </Suspense>
  );
}
