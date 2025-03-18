import React, { useState } from "react";
import { rateMessage } from "../utils/api";
import "../styles/Rating.css"; // <-- Import a dedicated CSS file (or use App.css)

function Rating({ messageId, userInput, assistantOutput }) {
  const [rating, setRating] = useState(null);
  const [hover, setHover] = useState(null);

  const handleRate = async (value) => {
    setRating(value);
    try {
      await rateMessage(value, messageId, userInput, assistantOutput);
    } catch (error) {
      console.error("Error rating message:", error);
    }
  };

  const tooltips = {
    1: "Not helpful at all",
    2: "Slightly helpful",
    3: "Moderately helpful",
    4: "Very helpful",
    5: "Extremely helpful",
  };

  return (
    <div className="ratingContainer">
      <div className="stars">
        {[...Array(5)].map((_, index) => {
          const ratingValue = index + 1;
          return (
            <span
              key={ratingValue}
              className={`star ${
                ratingValue <= (hover || rating) ? "active" : ""
              }`}
              onClick={() => handleRate(ratingValue)}
              onMouseEnter={() => setHover(ratingValue)}
              onMouseLeave={() => setHover(null)}
              title={tooltips[ratingValue]}
            >
              ★
            </span>
          );
        })}
      </div>
      {hover && <div className="tooltip">{tooltips[hover]}</div>}
    </div>
  );
}

export default Rating;
