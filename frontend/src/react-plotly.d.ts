declare module 'react-plotly.js' {
    import { Component } from 'react';
    import { PlotParams } from 'plotly.js';

    export interface PlotProps extends Partial<PlotParams> {
        data: any[];
        layout?: any;
        config?: any;
        frames?: any[];
        onInitialized?: (figure: any, graphDiv: HTMLElement) => void;
        onUpdate?: (figure: any, graphDiv: HTMLElement) => void;
        onPurge?: (figure: any, graphDiv: HTMLElement) => void;
        onError?: (err: any) => void;
        useResizeHandler?: boolean;
        style?: React.CSSProperties;
        className?: string;
        divId?: string;
    }

    export default class Plot extends Component<PlotProps> { }
}
