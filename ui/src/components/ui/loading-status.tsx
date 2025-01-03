'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { Text, Flex } from '@radix-ui/themes'
import lottie from 'lottie-web';
import { useEffect, useRef } from 'react';


export function LoadingStatus({ status }: { status: string }) {
  const animationContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (animationContainer.current && !animationContainer.current.getAttribute('data-loaded')) {
      lottie.loadAnimation({
        container: animationContainer.current,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'https://lottie.host/01f0ed75-121a-4849-8690-7ac12d3e71b4/PS1fjwmeyT.json'
      });
      animationContainer.current.setAttribute('data-loaded', 'true');
    }
  }, []);


  return (
    <Flex direction={'row'} justify={'center'} height={'100vh'}>
      <Flex direction={'column'} justify={'center'} align={'center'}>
      <div ref={animationContainer} className='w-[40%]'></div>
      <AnimatePresence mode="wait">
        <motion.div
          key={status}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          <Text size={'8'}>
            {status}
          </Text>
        </motion.div>
      </AnimatePresence>
      </Flex>
    </Flex>
  )
}