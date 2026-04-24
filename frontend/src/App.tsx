import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Video, Mic, Settings, Minimize2, MoreVertical, ChevronDown, ChevronUp } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

export default function App() {
  return (
    <div className="min-h-screen bg-bg-base text-text-primary p-4 md:p-6 flex flex-col md:flex-row gap-6 font-sans">
      <VideoPanel />
      <StatsPanel />
    </div>
  );
}

function VideoPanel() {
  return (
    <div className="flex-1 bg-bg-panel rounded-2xl overflow-hidden border border-bg-panel-light relative min-h-[600px] shadow-lg flex flex-col">
      {/* Top Overlay Bar */}
      <div className="absolute top-0 inset-x-0 p-6 flex justify-between items-center z-20">
        <div className="flex items-center gap-4">
          {/* Progress bar line */}
          <div className="absolute top-0 left-0 h-1 bg-bg-panel-light w-full">
            <div className="h-full bg-accent-cyan w-[90%]"></div>
          </div>
          <span className="text-lg font-medium tracking-wide mt-2">Barbell Squat (Rep 14/15)</span>
        </div>
        <div className="bg-red-500/20 text-red-500 px-3 py-1 flex items-center gap-2 rounded-md font-medium text-sm mt-2 border border-red-500/30">
          LIVE
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
        </div>
      </div>

      {/* Main Image/Video Area */}
      <div className="relative flex-1 bg-black overflow-hidden group">
        <img 
          src="https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?q=80&w=2069&auto=format&fit=crop" 
          alt="Athlete doing barbell squat" 
          className="absolute inset-0 w-full h-full object-cover object-center opacity-70 group-hover:opacity-80 transition-opacity duration-700"
          referrerPolicy="no-referrer"
        />
        
        {/* Simulated Pose Skeleton SVG */}
        <svg className="absolute inset-x-0 bottom-0 top-[10%] w-full h-[90%] pointer-events-none drop-shadow-lg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMax meet">
          {/* Cyan Left side */}
          <path d="M45,20 L40,35 L35,55 L38,75 L45,85" fill="none" stroke="var(--color-accent-cyan)" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M45,20 L35,22 L25,35" fill="none" stroke="var(--color-accent-cyan)" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" />
          {/* Magenta Right Side */}
          <path d="M55,20 L60,35 L62,55 L58,75 L54,85" fill="none" stroke="var(--color-accent-magenta)" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M55,20 L65,23 L70,36" fill="none" stroke="var(--color-accent-magenta)" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" />
          {/* Connection */}
          <line x1="45" y1="20" x2="55" y2="20" stroke="var(--color-accent-cyan)" strokeWidth="0.8" />
          
          {/* Nodes */}
          {/* Left leg & arm */}
          <circle cx="45" cy="20" r="1.5" fill="var(--color-accent-cyan)" />
          <circle cx="40" cy="35" r="1.5" fill="var(--color-accent-cyan)" />
          <circle cx="35" cy="55" r="1.5" fill="var(--color-accent-cyan)" />
          <circle cx="38" cy="75" r="1.5" fill="var(--color-accent-cyan)" />
          <circle cx="45" cy="85" r="1.5" fill="var(--color-accent-cyan)" />
          <circle cx="35" cy="22" r="1.5" fill="var(--color-accent-cyan)" />
          <circle cx="25" cy="35" r="1.5" fill="var(--color-accent-cyan)" />
          
          {/* Right leg & arm */}
          <circle cx="55" cy="20" r="1.5" fill="var(--color-accent-magenta)" />
          <circle cx="60" cy="35" r="1.5" fill="var(--color-accent-magenta)" />
          <circle cx="62" cy="55" r="1.5" fill="var(--color-accent-magenta)" />
          <circle cx="58" cy="75" r="1.5" fill="var(--color-accent-magenta)" />
          <circle cx="54" cy="85" r="1.5" fill="var(--color-accent-magenta)" />
          <circle cx="65" cy="23" r="1.5" fill="var(--color-accent-magenta)" />
          <circle cx="70" cy="36" r="1.5" fill="var(--color-accent-magenta)" />
        </svg>

        {/* Coach Nova Overlay Card */}
        <div className="absolute bottom-24 right-8 w-72 bg-bg-panel/90 backdrop-blur-md rounded-xl p-4 border border-bg-panel-light shadow-2xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="relative">
              <img src="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100&h=100&fit=crop" alt="Coach Nova" className="w-10 h-10 rounded-full border-2 border-accent-cyan object-cover" />
              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-accent-cyan rounded-full border-2 border-bg-panel"></div>
            </div>
            <div>
              <h4 className="text-sm font-bold tracking-wide uppercase">Coach Nova</h4>
            </div>
          </div>
          <div className="bg-bg-panel-light/50 rounded-lg p-3 text-sm text-text-secondary leading-relaxed border border-white/5">
            <span className="text-accent-green font-medium">Nova:</span> Great depth, Sarah! Focus on core engagement on the ascent. 1 Rep to go!
          </div>
          <div className="mt-2 bg-bg-panel-light/50 rounded-lg p-3 text-sm text-text-secondary leading-relaxed border border-white/5 flex items-start">
             Focus on keeping chest up during ascent.
          </div>
        </div>

        {/* Bottom Controls */}
        <div className="absolute bottom-8 left-8 flex items-center gap-4">
          <div className="flex bg-bg-panel/80 backdrop-blur-md border border-bg-panel-light rounded-full p-2 shadow-xl">
             <button className="w-10 h-10 flex items-center justify-center hover:bg-bg-panel-light rounded-full transition-colors">
               <Pause size={18} />
             </button>
             <button className="w-10 h-10 flex items-center justify-center hover:bg-bg-panel-light rounded-full transition-colors">
               <RotateCcw size={18} />
             </button>
          </div>
          
          <div className="w-10 h-10 rounded-full border-2 border-accent-cyan flex flex-col justify-center items-center gap-[2px]">
             <div className="w-[14px] h-[3px] bg-accent-cyan rounded-sm"></div>
             <div className="w-[14px] h-[3px] bg-accent-cyan hover:animate-pulse rounded-sm"></div>
          </div>
          <a href="http://localhost:5000" className="ml-4 px-4 py-2 bg-accent-cyan text-bg-base font-bold rounded-lg shadow-[0_0_15px_rgba(0,245,255,0.4)] hover:bg-white transition-colors flex items-center gap-2">
             <span>BACK TO DASHBOARD</span>
          </a>
        </div>
      </div>
    </div>
  );
}

function StatsPanel() {
  return (
    <div className="w-full md:w-[380px] lg:w-[420px] flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2 pb-4">
      <RepsOverviewCard />
      <BiomechanicsCard />
      <LiveTrackingCard />
    </div>
  );
}

function RepsOverviewCard() {
  return (
    <div className="bg-bg-panel rounded-2xl border border-bg-panel-light p-6 shadow-md flex gap-6">
      <div className="flex-1 flex flex-col items-center justify-center relative">
        <h3 className="text-text-secondary text-xs font-bold tracking-wider mb-2 absolute top-0 left-0 uppercase">Reps</h3>
        <button className="absolute top-0 right-0 text-text-secondary hover:text-white transition-colors">
          <MoreVertical size={16} />
        </button>
        {/* Custom Circular Progress */}
        <div className="relative w-36 h-36 mt-4 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90 pointer-events-none" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="none" stroke="var(--color-bg-panel-light)" strokeWidth="6" />
            <circle 
              cx="50" cy="50" r="45" fill="none" stroke="var(--color-accent-cyan)" strokeWidth="6" 
              strokeLinecap="round" strokeDasharray="283" strokeDashoffset="28" 
              className="drop-shadow-lg filter transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-mono font-bold text-accent-cyan drop-shadow-[0_0_8px_rgba(0,245,255,0.4)]">14</span>
            <span className="text-sm font-mono text-text-secondary">14/15</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col gap-4">
        {/* Form Score */}
        <div className="bg-bg-panel-light/30 rounded-xl p-4 border border-white/5 flex flex-col h-full justify-between relative overflow-hidden">
           <div className="absolute top-0 right-0 w-24 h-24 bg-accent-green/10 blur-xl rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
           <h3 className="text-text-secondary text-xs tracking-wider uppercase mb-1">Form</h3>
           <div className="flex items-baseline gap-2 mb-2">
             <span className="text-3xl font-mono font-bold text-accent-green">92<span className="text-lg">%</span></span>
             <span className="text-[10px] uppercase tracking-wider bg-accent-green/20 text-accent-green px-1.5 py-0.5 rounded-sm">Excellent</span>
           </div>
           <p className="text-xs text-text-secondary leading-snug">Maintaining neutral spine & depth</p>
        </div>
        
        {/* Time */}
        <div className="bg-bg-panel-light/30 rounded-xl p-4 border border-white/5 flex flex-col justify-center">
           <h3 className="text-text-secondary text-xs tracking-wider uppercase mb-1">Time</h3>
           <span className="text-2xl font-mono font-semibold tracking-wide text-white">00:48<span className="text-text-secondary">s</span></span>
        </div>
      </div>
    </div>
  );
}

// Dummy data for charts
const generateChartData = (points: number, variance: number, base: number) => {
  return Array.from({ length: points }).map((_, i) => ({
    val: base + Math.sin(i * 0.8) * variance + (Math.random() * variance * 0.5)
  }));
};

const depthData = generateChartData(15, 10, 80);
const kneeData = generateChartData(15, 5, 90);
const torsoData = generateChartData(15, 15, 60);

function BiomechanicsCard() {
  return (
    <div className="bg-bg-panel rounded-2xl border border-bg-panel-light p-6 shadow-md flex flex-col gap-4">
       <div className="flex justify-between items-center pb-2 border-b border-bg-panel-light">
          <h3 className="text-sm font-semibold tracking-wider uppercase text-white">Biomechanics Feedback</h3>
          <button className="text-text-secondary hover:text-white transition-colors"><ChevronUp size={16}/></button>
       </div>
       
       <div className="grid grid-cols-2 gap-x-6 gap-y-6">
          {/* Squat Depth */}
          <div className="flex flex-col">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Squat Depth</h4>
             <div className="flex items-baseline gap-2 mb-3">
               <span className="text-2xl font-mono font-bold text-accent-green">96<span className="text-sm">%</span></span>
               <span className="text-[10px] uppercase tracking-wider text-accent-green border border-accent-green/30 rounded-full px-2 py-0.5">Optimal</span>
             </div>
             <div className="h-12 w-full mt-auto">
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={depthData}>
                   <Line type="monotone" dataKey="val" stroke="var(--color-accent-green)" strokeWidth={2} dot={false} isAnimationActive={false}/>
                 </LineChart>
               </ResponsiveContainer>
             </div>
          </div>
          
          {/* Knee Alignment */}
          <div className="flex flex-col relative before:content-[''] before:absolute before:-left-3 before:h-full before:w-[1px] before:bg-bg-panel-light">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Knee Alignment</h4>
             <div className="flex items-baseline gap-2 mb-3">
               <span className="text-2xl font-mono font-bold text-accent-green">98<span className="text-sm">%</span></span>
               <span className="text-[10px] uppercase tracking-wider text-accent-green border border-accent-green/30 rounded-full px-2 py-0.5">Perfect</span>
             </div>
             <div className="h-12 w-full mt-auto relative">
                {/* Simulated center line indicator */}
                <div className="absolute inset-x-0 top-1/2 w-full h-[1px] bg-white/10"></div>
                <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-text-secondary opacity-50 z-10 hidden lg:block"></div>
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={kneeData}>
                   <Line type="monotone" dataKey="val" stroke="var(--color-accent-green)" strokeWidth={2} dot={false} isAnimationActive={false}/>
                 </LineChart>
               </ResponsiveContainer>
             </div>
          </div>

          <div className="col-span-2 h-[1px] bg-bg-panel-light"></div>

          {/* Torso Angle */}
          <div className="flex flex-col">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Torso Angle</h4>
             <div className="flex items-baseline gap-2 mb-3">
               <span className="text-2xl font-mono font-bold text-yellow-500">78°</span>
               <span className="text-[10px] uppercase tracking-wider text-yellow-500 border border-yellow-500/30 rounded-full px-2 py-0.5">Watch Lean</span>
             </div>
             <div className="h-12 w-full mt-auto relative">
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={torsoData}>
                   <Line type="monotone" dataKey="val" stroke="#eab308" strokeWidth={2} dot={false} isAnimationActive={false}/>
                 </LineChart>
               </ResponsiveContainer>
                {/* Playhead indicator */}
                <div className="absolute right-[20%] top-0 bottom-0 w-[1px] bg-yellow-500/50 z-10 flex flex-col items-center">
                  <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full mt-1"></div>
                </div>
             </div>
          </div>

          {/* Balance Dist. */}
          <div className="flex flex-col relative before:content-[''] before:absolute before:-left-3 before:h-full before:w-[1px] before:bg-bg-panel-light">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Balance Dist.</h4>
             <div className="flex items-center gap-2 mb-1">
               <span className="text-2xl font-bold tracking-wide">Center</span>
             </div>
             <p className="text-xs text-text-secondary mb-4">minimal shift</p>
             <div className="mt-auto px-2">
                {/* Horizontal slider visualization */}
                <div className="h-1 bg-bg-panel-light rounded-full w-full relative">
                   <div className="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.6)]"></div>
                   <div className="absolute inset-x-0 top-1/2 w-full flex justify-between px-1">
                      <div className="w-0.5 h-2 bg-text-secondary/30 -translate-y-1/2"></div>
                      <div className="w-0.5 h-3 bg-text-secondary -translate-y-1/2"></div>
                      <div className="w-0.5 h-2 bg-text-secondary/30 -translate-y-1/2"></div>
                   </div>
                </div>
             </div>
          </div>
       </div>
    </div>
  );
}

function LiveTrackingCard() {
  const previousReps = [
    { rep: 14, score: 92, status: 'good' },
    { rep: 13, score: 94, status: 'good' },
    { rep: 12, score: 91, status: 'good' },
    { rep: 11, score: 89, status: 'warning' },
    { rep: 10, score: 92, status: 'good' },
  ].reverse();

  return (
    <div className="bg-bg-panel rounded-2xl border border-bg-panel-light p-6 shadow-md flex flex-col pb-8">
      <div className="flex justify-between items-center pb-4 mb-4 border-b border-bg-panel-light">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-white">Live Pose Tracking</h3>
        <button className="text-text-secondary hover:text-white transition-colors"><ChevronUp size={16}/></button>
      </div>
      
      <div className="grid grid-cols-6 gap-2 w-full mt-2 relative">
         {/* Labels Column */}
         <div className="flex flex-col justify-end gap-6 text-[10px] text-text-secondary font-mono uppercase tracking-widest text-right pr-2">
            <span>Form</span>
            <span>Reps</span>
         </div>
         
         {/* Rep Columns */}
         {previousReps.map((r, i) => (
            <div key={i} className="flex flex-col items-center gap-6 relative group">
               {/* Pillar track */}
               <div className="absolute top-0 bottom-[10px] w-8 border border-white/5 rounded-t-full bg-white/[0.02]"></div>
               
               {/* Form Value wrapper overlay tracking curve */}
               <div className="h-16 flex items-end justify-center w-full relative z-10 pt-2">
                  <span className={`text-lg font-mono font-bold ${r.status === 'warning' ? 'text-text-secondary' : 'text-accent-green drop-shadow-[0_0_5px_rgba(0,255,102,0.3)]'}`}>
                     {r.score}
                  </span>
                  {/* Top dot */}
                  <div className={`absolute -top-1 w-2 h-2 rounded-full ${r.status === 'warning' ? 'bg-text-secondary' : 'bg-accent-green shadow-[0_0_8px_rgba(0,255,102,1)]'}`}></div>
               </div>
               
               {/* Rep Number */}
               <span className="text-sm font-mono text-text-secondary z-10">{r.rep}</span>
               
               {/* Connective line (simulated roughly with SVG) */}
               {i < previousReps.length - 1 && (
                  <svg className="absolute left-1/2 top-0 w-full h-8 overflow-visible pointer-events-none stroke-accent-green/50 opacity-50 z-0">
                     <line x1="0" y1="0" x2="100%" y2="4" strokeWidth="1.5" />
                  </svg>
               )}
            </div>
         ))}
      </div>
    </div>
  );
}
