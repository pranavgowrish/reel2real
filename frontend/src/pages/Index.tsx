import { motion } from "framer-motion";
import { TripForm } from "@/components/TripForm";
import heroVideo from "@/assets/travel-hero.mp4"; 
import { Compass } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen relative overflow-hidden bg-background">
      {/* Background Video with Sophisticated Overlay */}
      <div className="absolute inset-0 z-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src={heroVideo} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        {/* Multilayer overlay: Darker at top/bottom for legibility, lighter in center */}
        <div className="absolute inset-0 bg-black/30" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-black/60" />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="w-full py-6 px-8 flex justify-center items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <img
              src="logo2.png"
              alt="Logo"
              className="h-10 md:h-12 w-auto"
            />
          </motion.div>
          
        </header>

        {/* Main Content */}
        <main className="flex-1 flex flex-col items-center justify-center px-4 max-w-5xl mx-auto w-full text-center">
          
          {/* Sub-header / Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-12"
          >
            <div className="hidden md:flex items-center gap-2 text-white/80 text-sm font-medium px-4 py-2 rounded-3xl border border-white/20">
              <p className="text-sm md:text-base text-white font-medium leading-relaxed max-w-xl">
                A fast and automated itinerary creator that optimizes your route for the ultimate adventure.
              </p>
            </div>
          </motion.div>

          {/* Headline */}
          <div className="relative mb-12">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="text-5xl md:text-7xl lg:text-8xl font-black text-white tracking-tighter"
              style={{ lineHeight: '0.9' }}
            >
              <span className="block mb-2">Turn Your</span>
              <span className="block pb-2 bg-gradient-to-r from-orange-400 via-orange-500 to-primary bg-clip-text text-transparent italic px-4">
                Dream Trip
              </span>
              <span className="block mt-2">Into Reality.</span>
            </motion.h1>
          </div>

          {/* Trip Form Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="w-full max-w-4xl"
          >
            <div className="bg-white/10 dark:bg-background/100 p-2 md:p-4 rounded-[2.5rem] shadow-[0_20px_20px_rgba(0,0,0,0.08)] border border-white/20">
              <TripForm />
            </div>
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="py-8 text-center">
          <p className="text-white/40 text-xs uppercase tracking-[0.2em]">
            &copy; 2026 Reel-To-Real AI • Powered by Global Travel Data
          </p>
        </footer>
      </div>
      
      {/* Subtle Background Animation */}
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-primary/20 blur-[150px] -z-10 rounded-full animate-pulse" />
      <div className="absolute top-1/4 left-0 w-64 h-64 bg-orange-500/10 blur-[120px] -z-10 rounded-full" />
    </div>
  );
};

export default Index;
