import { useState } from "react";

export default function useGameViewOptions() {
  const [showRecordPanel, setShowRecordPanel] = useState<boolean>(true);
  const [showCoordInsideCell, setShowCoordInsideCell] = useState<boolean>(false);
  const [showDropHighlight, setShowDropHighlight] = useState<boolean>(true);
  const [showEatHighlight, setShowEatHighlight] = useState<boolean>(true);
  const [showMuzzleHighlight, setShowMuzzleHighlight] = useState<boolean>(true);
  const [showFireHighlight, setShowFireHighlight] = useState<boolean>(true);
  const [showArrowHints, setShowArrowHints] = useState<boolean>(true);
  const [showHoverPreview, setShowHoverPreview] = useState<boolean>(true);
  const [showCannonHoverEnhance, setShowCannonHoverEnhance] = useState<boolean>(true);
  const [compactSidebar, setCompactSidebar] = useState<boolean>(false);
  const [recordCollapsed, setRecordCollapsed] = useState<boolean>(false);

  return {
    showRecordPanel,
    setShowRecordPanel,
    showCoordInsideCell,
    setShowCoordInsideCell,
    showDropHighlight,
    setShowDropHighlight,
    showEatHighlight,
    setShowEatHighlight,
    showMuzzleHighlight,
    setShowMuzzleHighlight,
    showFireHighlight,
    setShowFireHighlight,
    showArrowHints,
    setShowArrowHints,
    showHoverPreview,
    setShowHoverPreview,
    showCannonHoverEnhance,
    setShowCannonHoverEnhance,
    compactSidebar,
    setCompactSidebar,
    recordCollapsed,
    setRecordCollapsed
  };
}