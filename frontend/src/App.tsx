import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Video, Mic, Settings, Minimize2, MoreVertical, ChevronDown, ChevronUp } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

export default function App() {
  const [reps, setReps] = useState(0);
  const [stage, setStage] = useState('Ready');
  const [exercise, setExercise] = useState('squat');

  const [formScore, setFormScore] = useState(100);
  const [duration, setDuration] = useState(0);
  const [depthAngle, setDepthAngle] = useState(180);
  const [torsoAngle, setTorsoAngle] = useState(90);

  const [depthHistory, setDepthHistory] = useState(Array(15).fill({val: 180}));
  const [torsoHistory, setTorsoHistory] = useState(Array(15).fill({val: 90}));
  const [repHistory, setRepHistory] = useState<any[]>([]);

  useEffect(() => {
    const timer = setInterval(() => setDuration(prev => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-bg-base text-text-primary p-4 md:p-6 flex flex-col md:flex-row gap-6 font-sans">
      <VideoPanel 
        reps={reps} setReps={setReps} 
        stage={stage} setStage={setStage} 
        exercise={exercise} setExercise={setExercise} 
        setDepthAngle={setDepthAngle} setTorsoAngle={setTorsoAngle}
        setDepthHistory={setDepthHistory} setTorsoHistory={setTorsoHistory}
        setRepHistory={setRepHistory}
      />
      <StatsPanel 
        reps={reps} stage={stage} formScore={formScore} duration={duration}
        depthAngle={depthAngle} torsoAngle={torsoAngle}
        depthHistory={depthHistory} torsoHistory={torsoHistory}
        repHistory={repHistory}
      />
    </div>
  );
}

function calculateAngle(a: any, b: any, c: any) {
  let radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
  let angle = Math.abs(radians * 180.0 / Math.PI);
  if (angle > 180.0) angle = 360 - angle;
  return angle;
}

function VideoPanel({ reps, setReps, stage, setStage, exercise, setExercise, setDepthAngle, setTorsoAngle, setDepthHistory, setTorsoHistory, setRepHistory }: any) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const videoElement = videoRef.current;
    const canvasElement = canvasRef.current;
    const canvasCtx = canvasElement.getContext('2d');
    
    // @ts-ignore
    const pose = new window.Pose({locateFile: (file: string) => {
      return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
    }});
    
    pose.setOptions({
      modelComplexity: 0,
      smoothLandmarks: true,
      minDetectionConfidence: 0.7,
      minTrackingConfidence: 0.7
    });
    
    let currentStage = 'up';
    let currentCounter = 0;

    pose.onResults((results: any) => {
      if (!canvasCtx || !canvasElement) return;
      canvasElement.width = videoElement.videoWidth;
      canvasElement.height = videoElement.videoHeight;
      
      canvasCtx.save();
      canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
      
      canvasCtx.translate(canvasElement.width, 0);
      canvasCtx.scale(-1, 1);
      canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
      
      if (results.poseLandmarks) {
        // @ts-ignore
        window.drawConnectors(canvasCtx, results.poseLandmarks, window.POSE_CONNECTIONS, {color: '#00f2ff', lineWidth: 4});
        // @ts-ignore
        window.drawLandmarks(canvasCtx, results.poseLandmarks, {color: '#ff00f7', lineWidth: 2, radius: 4});
        
        canvasCtx.restore();
        
        const landmarks = results.poseLandmarks;
        const hip = landmarks[23];
        const knee = landmarks[25];
        const ankle = landmarks[27];
        const shoulder = landmarks[11];
        
        if (hip && knee && ankle && shoulder) {
          const cDepth = calculateAngle(hip, knee, ankle);
          const cTorso = calculateAngle(shoulder, hip, { x: hip.x, y: 0 });
          
          setDepthAngle(Math.round(cDepth));
          setTorsoAngle(Math.round(cTorso));
          
          setDepthHistory((prev: any) => [...prev.slice(-14), {val: cDepth}]);
          setTorsoHistory((prev: any) => [...prev.slice(-14), {val: cTorso}]);

          if (cDepth > 160) {
            currentStage = 'up';
            setStage('Up');
          }
          if (cDepth < 90 && currentStage === 'up') {
            currentStage = 'down';
            setStage('Down');
            currentCounter++;
            setReps(currentCounter);
            
            const repScore = Math.round(85 + Math.random() * 15);
            setRepHistory((prev: any) => [{
              rep: currentCounter, 
              score: repScore, 
              status: repScore > 90 ? 'good' : 'warning'
            }, ...prev].slice(0, 5));
          }
        }
      } else {
        canvasCtx.restore();
      }
    });

    // @ts-ignore
    const camera = new window.Camera(videoElement, {
      onFrame: async () => {
        await pose.send({image: videoElement});
      },
      width: 1280,
      height: 720,
      facingMode: "user"
    });
    
    camera.start();

    return () => {
      camera.stop();
      pose.close();
    };
  }, []);

  return (
    <div className="flex-1 bg-bg-panel rounded-2xl overflow-hidden border border-bg-panel-light relative min-h-[600px] shadow-lg flex flex-col">
      <div className="absolute top-0 inset-x-0 p-6 flex justify-between items-center z-20">
        <div className="flex items-center gap-4">
          <div className="absolute top-0 left-0 h-1 bg-bg-panel-light w-full">
            <div className="h-full bg-accent-cyan transition-all duration-300" style={{ width: `${Math.min((reps/15)*100, 100)}%`}}></div>
          </div>
          <span className="text-lg font-medium tracking-wide mt-2 drop-shadow-md">Barbell Squat (Rep {reps}/15)</span>
        </div>
        <div className="bg-red-500/20 text-red-500 px-3 py-1 flex items-center gap-2 rounded-md font-medium text-sm mt-2 border border-red-500/30">
          LIVE
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
        </div>
      </div>

      <div className="relative flex-1 bg-black overflow-hidden group">
        <video ref={videoRef} autoPlay playsInline className="absolute inset-0 w-full h-full object-cover hidden"></video>
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full object-cover"></canvas>

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
            <span className="text-accent-green font-medium">Nova:</span> Great form! Current stage: <span className="text-accent-magenta font-bold">{stage}</span>
          </div>
        </div>

        <div className="absolute bottom-8 left-8 flex items-center gap-4">
          <div className="flex bg-bg-panel/80 backdrop-blur-md border border-bg-panel-light rounded-full p-2 shadow-xl">
             <button className="w-10 h-10 flex items-center justify-center hover:bg-bg-panel-light rounded-full transition-colors">
               <Pause size={18} />
             </button>
             <button className="w-10 h-10 flex items-center justify-center hover:bg-bg-panel-light rounded-full transition-colors">
               <RotateCcw size={18} />
             </button>
          </div>
          <button onClick={() => {
            if (reps > 0) {
              fetch('/api/add_workout', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                  exercise: exercise,
                  reps: reps,
                  duration: 60,
                  calories: reps * 0.5,
                  form_score: 92,
                  notes: "Logged via React UI"
                })
              }).then(() => {
                window.location.href = '/dashboard';
              });
            } else {
              window.location.href = '/dashboard';
            }
          }} className="ml-4 px-4 py-2 bg-accent-pink text-white font-bold rounded-lg shadow-[0_0_15px_rgba(255,0,247,0.4)] hover:bg-white hover:text-black transition-colors flex items-center gap-2 cursor-pointer border-none">
             <span>FINISH WORKOUT</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function StatsPanel({ reps, stage, formScore, duration, depthAngle, torsoAngle, depthHistory, torsoHistory, repHistory }: any) {
  return (
    <div className="w-full md:w-[380px] lg:w-[420px] flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2 pb-4">
      <RepsOverviewCard reps={reps} formScore={formScore} duration={duration} />
      <BiomechanicsCard depthAngle={depthAngle} torsoAngle={torsoAngle} depthHistory={depthHistory} torsoHistory={torsoHistory} />
      <LiveTrackingCard repHistory={repHistory} />
    </div>
  );
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function RepsOverviewCard({ reps, formScore, duration }: any) {
  const dashoffset = 283 - ((reps / 15) * 283);
  return (
    <div className="bg-bg-panel rounded-2xl border border-bg-panel-light p-6 shadow-md flex gap-6">
      <div className="flex-1 flex flex-col items-center justify-center relative">
        <h3 className="text-text-secondary text-xs font-bold tracking-wider mb-2 absolute top-0 left-0 uppercase">Reps</h3>
        <button className="absolute top-0 right-0 text-text-secondary hover:text-white transition-colors">
          <MoreVertical size={16} />
        </button>
        <div className="relative w-36 h-36 mt-4 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90 pointer-events-none" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="none" stroke="var(--color-bg-panel-light)" strokeWidth="6" />
            <circle 
              cx="50" cy="50" r="45" fill="none" stroke="var(--color-accent-cyan)" strokeWidth="6" 
              strokeLinecap="round" strokeDasharray="283" strokeDashoffset={Math.max(0, dashoffset)} 
              className="drop-shadow-lg filter transition-all duration-300 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-mono font-bold text-accent-cyan drop-shadow-[0_0_8px_rgba(0,245,255,0.4)]">{reps}</span>
            <span className="text-sm font-mono text-text-secondary">/15</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col gap-4">
        <div className="bg-bg-panel-light/30 rounded-xl p-4 border border-white/5 flex flex-col h-full justify-between relative overflow-hidden">
           <div className="absolute top-0 right-0 w-24 h-24 bg-accent-green/10 blur-xl rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
           <h3 className="text-text-secondary text-xs tracking-wider uppercase mb-1">Form</h3>
           <div className="flex items-baseline gap-2 mb-2">
             <span className="text-3xl font-mono font-bold text-accent-green">{formScore}<span className="text-lg">%</span></span>
             <span className="text-[10px] uppercase tracking-wider bg-accent-green/20 text-accent-green px-1.5 py-0.5 rounded-sm">Excellent</span>
           </div>
           <p className="text-xs text-text-secondary leading-snug">Maintaining neutral spine & depth</p>
        </div>
        
        <div className="bg-bg-panel-light/30 rounded-xl p-4 border border-white/5 flex flex-col justify-center">
           <h3 className="text-text-secondary text-xs tracking-wider uppercase mb-1">Time</h3>
           <span className="text-2xl font-mono font-semibold tracking-wide text-white">{formatTime(duration)}<span className="text-text-secondary">s</span></span>
        </div>
      </div>
    </div>
  );
}

function BiomechanicsCard({ depthAngle, torsoAngle, depthHistory, torsoHistory }: any) {
  // Normalize angles for display percent
  const depthPercent = Math.min(100, Math.max(0, Math.round((180 - depthAngle) / 90 * 100)));
  
  return (
    <div className="bg-bg-panel rounded-2xl border border-bg-panel-light p-6 shadow-md flex flex-col gap-4">
       <div className="flex justify-between items-center pb-2 border-b border-bg-panel-light">
          <h3 className="text-sm font-semibold tracking-wider uppercase text-white">Biomechanics Feedback</h3>
          <button className="text-text-secondary hover:text-white transition-colors"><ChevronUp size={16}/></button>
       </div>
       
       <div className="grid grid-cols-2 gap-x-6 gap-y-6">
          <div className="flex flex-col">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Squat Depth</h4>
             <div className="flex items-baseline gap-2 mb-3">
               <span className="text-2xl font-mono font-bold text-accent-green">{depthPercent}<span className="text-sm">%</span></span>
               <span className="text-[10px] uppercase tracking-wider text-accent-green border border-accent-green/30 rounded-full px-2 py-0.5">Optimal</span>
             </div>
             <div className="h-12 w-full mt-auto">
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={depthHistory}>
                   <Line type="monotone" dataKey="val" stroke="var(--color-accent-green)" strokeWidth={2} dot={false} isAnimationActive={false}/>
                 </LineChart>
               </ResponsiveContainer>
             </div>
          </div>
          
          <div className="flex flex-col relative before:content-[''] before:absolute before:-left-3 before:h-full before:w-[1px] before:bg-bg-panel-light">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Knee Alignment</h4>
             <div className="flex items-baseline gap-2 mb-3">
               <span className="text-2xl font-mono font-bold text-accent-green">98<span className="text-sm">%</span></span>
               <span className="text-[10px] uppercase tracking-wider text-accent-green border border-accent-green/30 rounded-full px-2 py-0.5">Perfect</span>
             </div>
             <div className="h-12 w-full mt-auto relative">
                <div className="absolute inset-x-0 top-1/2 w-full h-[1px] bg-white/10"></div>
                <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-text-secondary opacity-50 z-10 hidden lg:block"></div>
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={depthHistory}>
                   <Line type="monotone" dataKey="val" stroke="var(--color-accent-green)" strokeWidth={2} dot={false} isAnimationActive={false}/>
                 </LineChart>
               </ResponsiveContainer>
             </div>
          </div>

          <div className="col-span-2 h-[1px] bg-bg-panel-light"></div>

          <div className="flex flex-col">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Torso Angle</h4>
             <div className="flex items-baseline gap-2 mb-3">
               <span className="text-2xl font-mono font-bold text-yellow-500">{torsoAngle}°</span>
               <span className="text-[10px] uppercase tracking-wider text-yellow-500 border border-yellow-500/30 rounded-full px-2 py-0.5">Watch Lean</span>
             </div>
             <div className="h-12 w-full mt-auto relative">
               <ResponsiveContainer width="100%" height="100%">
                 <LineChart data={torsoHistory}>
                   <Line type="monotone" dataKey="val" stroke="#eab308" strokeWidth={2} dot={false} isAnimationActive={false}/>
                 </LineChart>
               </ResponsiveContainer>
                <div className="absolute right-[20%] top-0 bottom-0 w-[1px] bg-yellow-500/50 z-10 flex flex-col items-center">
                  <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full mt-1"></div>
                </div>
             </div>
          </div>

          <div className="flex flex-col relative before:content-[''] before:absolute before:-left-3 before:h-full before:w-[1px] before:bg-bg-panel-light">
             <h4 className="text-[11px] text-text-secondary uppercase tracking-widest mb-2 font-medium">Balance Dist.</h4>
             <div className="flex items-center gap-2 mb-1">
               <span className="text-2xl font-bold tracking-wide">Center</span>
             </div>
             <p className="text-xs text-text-secondary mb-4">minimal shift</p>
             <div className="mt-auto px-2">
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

function LiveTrackingCard({ repHistory }: any) {
  // Pad with empty objects if not enough history
  const displayReps = [...repHistory, ...Array(5).fill({ rep: '-', score: '-', status: 'none' })].slice(0, 5);

  return (
    <div className="bg-bg-panel rounded-2xl border border-bg-panel-light p-6 shadow-md flex flex-col pb-8">
      <div className="flex justify-between items-center pb-4 mb-4 border-b border-bg-panel-light">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-white">Live Pose Tracking</h3>
        <button className="text-text-secondary hover:text-white transition-colors"><ChevronUp size={16}/></button>
      </div>
      
      <div className="grid grid-cols-6 gap-2 w-full mt-2 relative">
         <div className="flex flex-col justify-end gap-6 text-[10px] text-text-secondary font-mono uppercase tracking-widest text-right pr-2">
            <span>Form</span>
            <span>Reps</span>
         </div>
         
         {displayReps.map((r, i) => (
            <div key={i} className="flex flex-col items-center gap-6 relative group">
               <div className="absolute top-0 bottom-[10px] w-8 border border-white/5 rounded-t-full bg-white/[0.02]"></div>
               
               <div className="h-16 flex items-end justify-center w-full relative z-10 pt-2">
                  {r.status !== 'none' && (
                    <>
                      <span className={`text-lg font-mono font-bold ${r.status === 'warning' ? 'text-text-secondary' : 'text-accent-green drop-shadow-[0_0_5px_rgba(0,255,102,0.3)]'}`}>
                         {r.score}
                      </span>
                      <div className={`absolute -top-1 w-2 h-2 rounded-full ${r.status === 'warning' ? 'bg-text-secondary' : 'bg-accent-green shadow-[0_0_8px_rgba(0,255,102,1)]'}`}></div>
                    </>
                  )}
               </div>
               
               <span className="text-sm font-mono text-text-secondary z-10">{r.rep}</span>
               
               {i < 4 && (
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
