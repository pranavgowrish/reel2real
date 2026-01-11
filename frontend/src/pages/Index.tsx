import { motion } from "framer-motion";
import { TripForm } from "@/components/TripForm";
import heroImage from "@/assets/hero-travel.jpg";

const Index = () => {
  return (
    <div className="min-h-screen relative overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-background/70 to-background/95" />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        <header className="py-4 flex items-center justify-center px-4">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex justify-center"
          >
            <img src="logo2.png" alt="Logo" className="size-1/3" />
          </motion.div>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center px-4 pb-48">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-center max-w-2xl mb-8"
          >
            <p className="text-base text-muted-foreground">
              A fast and automative itinerary creator that analyzes thousands of websites
              to find the perfect activities matching your vibe and optimizes
              your route for the ultimate adventure.
            </p>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-4xl md:text-6xl lg:text-6xl font-bold text-center mb-12"
          >
            <span className="block text-foreground">Turn Your</span>
            <span className="block bg-gradient-to-r from-primary via-accent-foreground to-primary bg-clip-text text-transparent">
              Dream Trip
            </span>
            <span className="block text-foreground">Into Reality</span>
          </motion.h1>

          <TripForm />
        </main>

        <footer className="py-4 text-center text-sm text-muted-foreground">
        </footer>
      </div>
    </div>
  );
};

export default Index;
