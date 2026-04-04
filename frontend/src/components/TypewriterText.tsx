import { useState, useEffect } from "react";

interface TypewriterTextProps {
  text: string;
  speed?: number;
}

const TypewriterText = ({ text, speed = 20 }: TypewriterTextProps) => {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setDisplayed(text.slice(0, i + 1));
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        setDone(true);
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span>
      {displayed}
      {!done && <span className="typewriter-cursor" />}
    </span>
  );
};

export default TypewriterText;
