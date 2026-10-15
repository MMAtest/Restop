/** Inspired by Motion Primitives Animated Number (ibelick/motion-primitives, MIT).
 * Reimplemented for Restop's plain JS and French numeric formatting.
 * License: https://github.com/ibelick/motion-primitives/blob/main/LICENCE.md
 */
import React, {useEffect} from 'react';
import {motion, useReducedMotion, useSpring, useTransform} from 'motion/react';

export default function AnimatedNumber({value=0, className='', suffix=''}) {
  const numeric = Number.isFinite(Number(value)) ? Number(value) : 0;
  const reduceMotion = useReducedMotion();
  const spring = useSpring(numeric, {stiffness:260, damping:34, mass:0.75});
  const display = useTransform(spring, latest => Math.round(latest).toLocaleString('fr-FR'));
  useEffect(() => {spring.set(numeric)}, [numeric, spring]);
  return <span className={className} style={{fontVariantNumeric:'tabular-nums'}}>
    {reduceMotion ? numeric.toLocaleString('fr-FR') : <motion.span>{display}</motion.span>}{suffix}
  </span>;
}
