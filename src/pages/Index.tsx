import { motion } from "framer-motion";
import { Logo } from "@/components/Logo";
import { TripForm } from "@/components/TripForm";
import heroImage from "@/assets/hero-travel.jpg";

const Index = () => {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Image with Overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/70 to-background/95" />
      </div>

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="py-6 px-4">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex justify-center"
          >
            <Logo className="scale-110" />
          </motion.div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex flex-col items-center justify-center px-4 pb-12">
          {/* Description */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-center max-w-2xl mb-8"
          >
            <p className="text-lg text-muted-foreground">
              AI-powered itinerary creator that analyzes thousands of websites
              to find the perfect activities matching your vibe and optimizes
              your route for the ultimate adventure.
            </p>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold text-center mb-12"
          >
            <span className="block text-foreground">Turn Your</span>
            <span className="block bg-gradient-to-r from-primary via-accent-foreground to-primary bg-clip-text text-transparent">
              Dream Trip
            </span>
            <span className="block text-foreground">Into Reality</span>
          </motion.h1>

          {/* Trip Form */}
          <TripForm />
        </main>

        {/* Footer */}
        <footer className="py-4 text-center text-sm text-muted-foreground">
          <p>Built for the Entertainment Track Hackathon 🎬</p>
        </footer>
      </div>
    </div>
  );
};

export default Index;
