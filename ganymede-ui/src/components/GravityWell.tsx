'use client';

import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { GSSState } from '../types/ganymede';

interface GravityWellProps {
  config: GSSState | null;
  overrides: { drawRate: number; mitigation: number };
  scanColor: string;
}

export function GravityWell({ config, overrides, scanColor }: GravityWellProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const entitiesGroupRef = useRef<THREE.Group>(null);
  const legPlaneRef = useRef<THREE.Mesh>(null);
  
  const gridSize = 40;
  const segments = 80;
  
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(gridSize, gridSize, segments, segments);
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, []);

  const originalPositions = useMemo(() => {
    return new Float32Array(geometry.attributes.position.array);
  }, [geometry]);

  // Nodes rendering
  const renderNodes = useMemo(() => {
    if (!config) return null;
    return config.topological_entities.map((entity) => {
      const color = entity.type === 'Industrial_Sink' ? '#63b3ed' : 
                    entity.type === 'Agricultural_Peripheral' ? '#f56565' : '#10b981';
      const size = entity.type === 'Industrial_Sink' ? 0.6 : 0.25;
      
      return (
        <mesh key={entity.node_id} position={[entity.coordinates.x, 0, entity.coordinates.z]} name={entity.node_id}>
          <icosahedronGeometry args={[size, 1]} />
          <meshStandardMaterial 
            color={color} 
            emissive={color} 
            emissiveIntensity={entity.luminosity * 2.5} 
            transparent
            opacity={0.9}
          />
        </mesh>
      );
    });
  }, [config]);

  useFrame((state) => {
    if (!config) return;

    const time = state.clock.getElapsedTime();
    const posAttribute = geometry.attributes.position;
    
    // Use Overrides if available, otherwise fallback to config
    const currentDrawRate = overrides.drawRate;
    const currentMitigation = overrides.mitigation;
    const threshold = config.physics_logic.failure_threshold;
    const ambient = config.environmental_baseline.ambient_depletion;

    // 1. Update Topological Grid
    for (let i = 0; i < posAttribute.count; i++) {
      const x = originalPositions[i * 3];
      const z = originalPositions[i * 3 + 2];
      
      let depth = 0;
      
      // Industrial Sink Suction (Dn = sum( L_ind / (dist + epsilon) ) * (1 - M_leg))
      config.topological_entities.forEach(entity => {
        if (entity.type === 'Industrial_Sink') {
          const dist = Math.sqrt(Math.pow(x - entity.coordinates.x, 2) + Math.pow(z - entity.coordinates.z, 2));
          const pull = (currentDrawRate / 180000) / (dist + 0.8);
          depth -= pull * (1 - currentMitigation);
        }
      });

      // Ambient "Fluid" Warp
      depth -= (ambient / 8) * Math.sin(x * 0.15 + time * 0.5) * Math.cos(z * 0.15 + time * 0.5);

      // System Failure Fracture
      let finalX = x;
      let finalZ = z;
      if (depth < threshold) {
        const intensity = Math.min(1.5, (threshold - depth) * 2);
        finalX += Math.sin(time * 30 + i) * 0.05 * intensity;
        finalZ += Math.cos(time * 30 + i) * 0.05 * intensity;
        // Visual "tear" effect by offsetting depth erratically
        depth += Math.tan(time * 5 + i * 0.1) * 0.02 * intensity;
      }

      posAttribute.setXYZ(i, finalX, depth, finalZ);
    }
    
    posAttribute.needsUpdate = true;
    geometry.computeVertexNormals();

    // 2. Update Entity Vertical Positions (Entanglement Logic)
    if (entitiesGroupRef.current) {
      entitiesGroupRef.current.children.forEach((child) => {
        const entity = config.topological_entities.find(e => e.node_id === child.name);
        if (entity) {
          const distToSink = Math.sqrt(Math.pow(child.position.x, 2) + Math.pow(child.position.z, 2));
          const pull = (currentDrawRate / 180000) / (distToSink + 0.8) * (1 - currentMitigation);
          child.position.y = -pull + 0.6 + Math.sin(time * 2 + child.position.x) * 0.05;
        }
      });
    }

    // 3. Update Legislative Plane (The Ceiling)
    if (legPlaneRef.current) {
      legPlaneRef.current.position.y = currentMitigation * 3 - 0.5;
      // Holographic pulse effect
      const pulse = 0.1 + Math.sin(time * 2) * 0.05;
      legPlaneRef.current.material.opacity = pulse + currentMitigation * 0.2;
    }

    if (meshRef.current) {
      meshRef.current.rotation.y = time * 0.03;
    }
  });

  const materialColor = useMemo(() => new THREE.Color(scanColor), [scanColor]);

  return (
    <group>
      {/* The Topological Grid */}
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial 
          color={materialColor}
          wireframe={true}
          transparent={true}
          opacity={0.5}
          emissive={materialColor}
          emissiveIntensity={0.6}
        />
      </mesh>

      {/* The Legislative Plane (HB-2041 Ceiling) */}
      <mesh ref={legPlaneRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[gridSize, gridSize]} />
        <meshStandardMaterial 
          color="#10b981" 
          transparent 
          opacity={0.2} 
          side={THREE.DoubleSide} 
          depthWrite={false}
        />
      </mesh>
      
      {/* Entangled Entities */}
      <group ref={entitiesGroupRef}>
        {renderNodes}
      </group>
    </group>
  );
}
