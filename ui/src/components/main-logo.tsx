import React from 'react';
import { cn } from '@/lib/utils';
import { Brain } from 'lucide-react';
import { Heading } from '@radix-ui/themes';
import * as Radix from '@radix-ui/themes';

interface MainLogoProps {
  variant?: 'vertical' | 'horizontal';
  className?: string;
}

export const MainLogo: React.FC<MainLogoProps> = ({ 
  variant = 'horizontal',
  className = '' 
}) => {
  return (
    <div className={cn(
      'flex items-center text-white',
      variant === 'vertical' ? 'flex-col text-center' : 'flex-row',
      className
    )}>
      <Brain className='pb-0 pr-2' size={variant === 'horizontal' ? 60 : 100} />
      <Radix.Separator orientation={variant === 'horizontal' ? 'vertical' : 'horizontal'}  size="4" />
      <Heading size={variant === 'horizontal' ? '9' : '9' } className='pb-2'>erudite</Heading>
    </div>
  );
};

export default MainLogo;