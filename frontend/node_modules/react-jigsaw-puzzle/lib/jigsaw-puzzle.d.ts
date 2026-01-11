import { FC } from 'react';
export interface JigsawPuzzleProps {
    /** Source of the image. Can be any URL or relative path. */
    imageSrc: string;
    /** The amount of rows the puzzle will have. Defaults to 3. */
    rows?: number;
    /** The amount of columns the puzzle with have. Defaults to 4. */
    columns?: number;
    onSolved?: () => void;
}
export declare const JigsawPuzzle: FC<JigsawPuzzleProps>;
//# sourceMappingURL=jigsaw-puzzle.d.ts.map