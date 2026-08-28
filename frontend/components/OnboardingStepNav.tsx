"use client";
import React from 'react';
export default function OnboardingStepNav({ prev, next }: { prev?: string; next?: string }) {
  return (
    <div className="onboarding-step-nav">
      {prev ? <a href={prev} className="btn ghost">Back</a> : <span />}
      {next ? <a href={next} className="btn primary">Continue</a> : null}
    </div>
  );
}
