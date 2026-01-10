import { motion } from "framer-motion";
import { Film, Image as ImageIcon } from "lucide-react";

interface MediaSidebarProps {
  images: Array<{ url: string; caption: string }>;
  videos: Array<{ youtubeId: string; title: string }>;
}

export const MediaSidebar = ({ images, videos }: MediaSidebarProps) => {
  return (
    <div className="space-y-6">
      {/* Videos Section */}
      <div className="space-y-3">
        {videos.map((video, index) => (
          <motion.div
            key={video.youtubeId}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.15 }}
            className="rounded-xl overflow-hidden shadow-lg border border-border"
          >
            <div className="aspect-[9/16] max-h-48">
              <iframe
                src={`https://www.youtube.com/embed/${video.youtubeId}?controls=0&modestbranding=1`}
                title={video.title}
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <p className="p-2 text-xs text-muted-foreground truncate bg-card">
              {video.title}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Images Section */}
      <div>
        <div className="grid grid-cols-2 gap-2">
          {images.map((image, index) => (
            <motion.div
              key={image.url}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="relative rounded-lg overflow-hidden shadow-md aspect-square group"
            >
              <img
                src={image.url}
                alt={image.caption}
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <p className="absolute bottom-2 left-2 right-2 text-xs text-white font-medium truncate">
                  {image.caption}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};
