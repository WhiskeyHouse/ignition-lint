/**
 * TypeScript definitions for Ignition Perspective Core Components (ia.*)
 * Generated from analysis of whk-distillery01-ignition-global perspective assets
 * 
 * Use these types for:
 * - IDE auto-completion and type checking
 * - Fine-tuning AI agents working with Ignition components
 * - Linting and validation of perspective view JSON files
 */

// Base interfaces
export interface ComponentPosition {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  basis?: string | number;
  grow?: number;
  shrink?: number;
  display?: boolean;
}

export interface ComponentStyle {
  classes?: string;
  margin?: number;
  padding?: number;
  width?: string;
  height?: string;
  overflow?: string;
  'user-select'?: string;
  alignSelf?: string;
}

export interface ComponentMeta {
  name?: string;
  tooltip?: {
    enabled?: boolean;
    location?: string;
    sustain?: number;
    text?: string;
  };
}

export interface ComponentBinding {
  type: 'property' | 'expr' | 'tag';
  config: any;
  transforms?: any[];
}

export interface ComponentPropConfig {
  [key: string]: {
    binding?: ComponentBinding;
    paramDirection?: 'input' | 'output' | 'inout';
    persistent?: boolean;
  };
}

export interface ComponentEvents {
  component?: Record<string, any>;
  dom?: Record<string, any>;
}

export interface ComponentBase {
  type: string;
  meta?: ComponentMeta;
  position?: ComponentPosition;
  props?: {
    style?: ComponentStyle;
    [key: string]: any;
  };
  propConfig?: ComponentPropConfig;
  events?: ComponentEvents;
  children?: ComponentBase[];
}

// Container Components
export interface FlexContainerProps {
  direction?: 'row' | 'column';
  justify?: string;
  alignItems?: string;
  wrap?: string;
  gap?: number;
  style?: ComponentStyle;
}

export interface FlexContainer extends ComponentBase {
  type: 'ia.container.flex';
  props?: FlexContainerProps;
}

export interface CoordContainer extends ComponentBase {
  type: 'ia.container.coord';
}

export interface BreakpointContainer extends ComponentBase {
  type: 'ia.container.breakpt';
}

export interface TabContainer extends ComponentBase {
  type: 'ia.container.tab';
}

// Display Components
export interface TextStyle {
  classes?: string;
  margin?: number;
  fontWeight?: string | number;
  fontSize?: string;
  color?: string;
  textAlign?: string;
}

export interface LabelProps {
  text?: string;
  textStyle?: TextStyle;
  style?: ComponentStyle;
}

export interface Label extends ComponentBase {
  type: 'ia.display.label';
  props?: LabelProps;
}

export interface IconProps {
  path?: string;
  color?: string;
  rotation?: number;
  size?: number;
  style?: ComponentStyle;
}

export interface Icon extends ComponentBase {
  type: 'ia.display.icon';
  props?: IconProps;
}

export interface EmbeddedView extends ComponentBase {
  type: 'ia.display.view';
  props?: {
    path?: string;
    params?: Record<string, any>;
    style?: ComponentStyle;
  };
}

export interface Table extends ComponentBase {
  type: 'ia.display.table';
  props?: {
    data?: any[];
    columns?: any[];
    style?: ComponentStyle;
  };
}

export interface FlexRepeater extends ComponentBase {
  type: 'ia.display.flex-repeater';
  props?: {
    instances?: any[];
    path?: string;
    style?: ComponentStyle;
  };
}

export interface IFrame extends ComponentBase {
  type: 'ia.display.iframe';
  props?: {
    src?: string;
    referrerPolicy?: string;
    style?: ComponentStyle;
  };
}

// Input Components
export interface ButtonProps {
  text?: string;
  enabled?: boolean;
  visible?: boolean;
  textStyle?: TextStyle;
  style?: ComponentStyle;
}

export interface Button extends ComponentBase {
  type: 'ia.input.button';
  props?: ButtonProps;
}

export interface OneShotButton extends ComponentBase {
  type: 'ia.input.oneshotbutton';
  props?: ButtonProps;
}

export interface TextFieldProps {
  text?: string;
  placeholder?: string;
  enabled?: boolean;
  visible?: boolean;
  style?: ComponentStyle;
}

export interface TextField extends ComponentBase {
  type: 'ia.input.text-field';
  props?: TextFieldProps;
}

export interface NumericEntryField extends ComponentBase {
  type: 'ia.input.numeric-entry-field';
  props?: {
    value?: number;
    format?: string;
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

export interface Dropdown extends ComponentBase {
  type: 'ia.input.dropdown';
  props?: {
    options?: any[];
    value?: any;
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

export interface Checkbox extends ComponentBase {
  type: 'ia.input.checkbox';
  props?: {
    selected?: boolean;
    text?: string;
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

export interface TextArea extends ComponentBase {
  type: 'ia.input.text-area';
  props?: {
    text?: string;
    placeholder?: string;
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

export interface DateTimeInput extends ComponentBase {
  type: 'ia.input.date-time-input';
  props?: {
    value?: string | Date;
    format?: string;
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

export interface MultiStateButton extends ComponentBase {
  type: 'ia.input.multi-state-button';
  props?: {
    controlValue?: any;
    states?: any[];
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

export interface ToggleSwitch extends ComponentBase {
  type: 'ia.input.toggle-switch';
  props?: {
    selected?: boolean;
    enabled?: boolean;
    visible?: boolean;
    style?: ComponentStyle;
  };
}

// Chart Components
export interface ChartSeries {
  name?: string;
  data?: any;
  render?: string;
  visible?: boolean;
  [key: string]: any;
}

export interface ChartAxis {
  name?: string;
  label?: {
    text?: string;
    enabled?: boolean;
  };
  visible?: boolean;
  [key: string]: any;
}

export interface XYChart extends ComponentBase {
  type: 'ia.chart.xy';
  props?: {
    dataSources?: Record<string, any>;
    series?: ChartSeries[];
    xAxes?: ChartAxis[];
    yAxes?: ChartAxis[];
    style?: ComponentStyle;
  };
}

export interface PieChart extends ComponentBase {
  type: 'ia.chart.pie';
  props?: {
    data?: any[];
    style?: ComponentStyle;
  };
}

// Navigation Components
export interface MenuTree extends ComponentBase {
  type: 'ia.navigation.menutree';
  props?: {
    items?: any[];
    style?: ComponentStyle;
  };
}

export interface HorizontalMenu extends ComponentBase {
  type: 'ia.navigation.horizontalmenu';
  props?: {
    items?: any[];
    style?: ComponentStyle;
  };
}

// Union types for all components
export type ContainerComponent = FlexContainer | CoordContainer | BreakpointContainer | TabContainer;

export type DisplayComponent = Label | Icon | EmbeddedView | Table | FlexRepeater | IFrame;

export type InputComponent = 
  | Button 
  | OneShotButton 
  | TextField 
  | NumericEntryField 
  | Dropdown 
  | Checkbox 
  | TextArea 
  | DateTimeInput 
  | MultiStateButton 
  | ToggleSwitch;

export type ChartComponent = XYChart | PieChart;

export type NavigationComponent = MenuTree | HorizontalMenu;

export type IAComponent = 
  | ContainerComponent 
  | DisplayComponent 
  | InputComponent 
  | ChartComponent 
  | NavigationComponent;

// View structure
export interface PerspectiveView {
  custom?: Record<string, any>;
  params?: Record<string, any>;
  propConfig?: ComponentPropConfig;
  props?: {
    defaultSize?: {
      width?: number;
      height?: number;
    };
    [key: string]: any;
  };
  root: IAComponent;
}

// Component registry for validation
export const IA_COMPONENT_TYPES = {
  // Containers (4 types)
  CONTAINERS: [
    'ia.container.flex',
    'ia.container.coord', 
    'ia.container.breakpt',
    'ia.container.tab'
  ],
  
  // Display (17 types)
  DISPLAY: [
    'ia.display.label',
    'ia.display.icon',
    'ia.display.view',
    'ia.display.table',
    'ia.display.flex-repeater',
    'ia.display.markdown',
    'ia.display.tree',
    'ia.display.image',
    'ia.display.iframe',
    'ia.display.tag-browse-tree',
    'ia.display.viewcanvas',
    'ia.display.progress',
    'ia.display.equipmentschedule',
    'ia.display.barcode',
    'ia.display.alarmstatustable',
    'ia.display.alarmjournaltable'
  ],
  
  // Input (12 types)
  INPUT: [
    'ia.input.button',
    'ia.input.dropdown',
    'ia.input.text-field',
    'ia.input.numeric-entry-field',
    'ia.input.checkbox',
    'ia.input.text-area',
    'ia.input.oneshotbutton',
    'ia.input.date-time-input',
    'ia.input.multi-state-button',
    'ia.input.toggle-switch',
    'ia.input.signature-pad',
    'ia.input.fileupload'
  ],
  
  // Charts (2 types)
  CHARTS: [
    'ia.chart.pie',
    'ia.chart.xy'
  ],
  
  // Navigation (2 types)
  NAVIGATION: [
    'ia.navigation.menutree',
    'ia.navigation.horizontalmenu'
  ]
} as const;

export const ALL_IA_COMPONENT_TYPES = [
  ...IA_COMPONENT_TYPES.CONTAINERS,
  ...IA_COMPONENT_TYPES.DISPLAY,
  ...IA_COMPONENT_TYPES.INPUT,
  ...IA_COMPONENT_TYPES.CHARTS,
  ...IA_COMPONENT_TYPES.NAVIGATION
] as const;

export type IAComponentType = typeof ALL_IA_COMPONENT_TYPES[number];