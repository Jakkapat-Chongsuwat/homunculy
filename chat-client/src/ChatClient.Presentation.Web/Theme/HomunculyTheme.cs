using MudBlazor;

namespace ChatClient.Presentation.Web.Theme;

/// <summary>
/// Homunculy AI - Modern Glassmorphism Dark Theme.
/// Style: Minimal dark with frosted glass effects and vibrant accents.
/// Typography: Plus Jakarta Sans (primary), Inter (fallback).
/// </summary>
public static class HomunculyTheme
{
    // Background & Surface (deep dark with subtle warmth)
    private const string BackgroundDark = "#0A0A0B";
    private const string SurfaceDark = "#141416";
    private const string SurfaceElevated = "#1C1C1F";
    
    // Border & Dividers (subtle glass edges)
    private const string BorderGlass = "rgba(255, 255, 255, 0.08)";
    private const string BorderMuted = "#2A2A2D";
    
    // Text hierarchy
    private const string TextWhite = "#FAFAFA";
    private const string TextMuted = "#94A3B8";
    private const string TextSubtle = "#64748B";
    
    // Accent colors (vibrant modern palette)
    private const string AccentPrimary = "#2563EB";      // Royal Blue
    private const string AccentPrimaryLight = "#3B82F6"; 
    private const string AccentSecondary = "#8B5CF6";    // Violet
    private const string AccentCTA = "#F97316";          // Orange (call-to-action)
    
    // Semantic colors
    private const string ErrorRed = "#EF4444";
    private const string SuccessGreen = "#10B981";
    private const string WarningAmber = "#F59E0B";
    private const string InfoBlue = "#0EA5E9";

    public static MudTheme Create() => new()
    {
        PaletteDark = new PaletteDark
        {
            Background = BackgroundDark,
            Surface = SurfaceDark,
            BackgroundGray = SurfaceElevated,
            
            Primary = AccentPrimary,
            PrimaryContrastText = TextWhite,
            PrimaryDarken = "#1D4ED8",
            PrimaryLighten = AccentPrimaryLight,
            
            Secondary = AccentSecondary,
            SecondaryContrastText = TextWhite,
            
            Tertiary = AccentCTA,
            TertiaryContrastText = TextWhite,
            
            TextPrimary = TextWhite,
            TextSecondary = TextMuted,
            TextDisabled = TextSubtle,
            
            ActionDefault = TextMuted,
            ActionDisabled = TextSubtle,
            ActionDisabledBackground = SurfaceDark,
            
            Divider = BorderMuted,
            DividerLight = BorderGlass,
            LinesDefault = BorderMuted,
            LinesInputs = BorderMuted,
            
            AppbarBackground = BackgroundDark,
            AppbarText = TextWhite,
            
            DrawerBackground = SurfaceDark,
            DrawerText = TextWhite,
            DrawerIcon = TextMuted,
            
            OverlayDark = "rgba(0,0,0,0.7)",
            OverlayLight = "rgba(255,255,255,0.05)",
            
            Error = ErrorRed,
            ErrorContrastText = TextWhite,
            Success = SuccessGreen,
            SuccessContrastText = TextWhite,
            Warning = WarningAmber,
            WarningContrastText = BackgroundDark,
            Info = InfoBlue,
            InfoContrastText = TextWhite,
            
            Dark = BackgroundDark,
            DarkContrastText = TextWhite,
        },
        
        PaletteLight = new PaletteLight
        {
            Primary = AccentPrimary,
            Secondary = AccentSecondary,
            Tertiary = AccentCTA,
            Background = "#FAFBFC",
            Surface = "#FFFFFF",
            TextPrimary = "#0F172A",
            TextSecondary = "#475569",
            Divider = "#E2E8F0",
            AppbarBackground = "#FFFFFF",
            AppbarText = "#0F172A",
        },
        
        Typography = new Typography
        {
            Default = new DefaultTypography
            {
                FontFamily = ["'Plus Jakarta Sans'", "Inter", "system-ui", "sans-serif"],
                FontSize = "0.875rem",
                FontWeight = "500",
                LineHeight = "1.6",
                LetterSpacing = "-0.01em"
            },
            H1 = new H1Typography
            {
                FontFamily = ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
                FontSize = "2.25rem",
                FontWeight = "700",
                LineHeight = "1.2",
                LetterSpacing = "-0.02em"
            },
            H2 = new H2Typography
            {
                FontFamily = ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
                FontSize = "1.75rem",
                FontWeight = "600",
                LetterSpacing = "-0.015em"
            },
            H3 = new H3Typography
            {
                FontFamily = ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
                FontSize = "1.25rem",
                FontWeight = "600"
            },
            Body1 = new Body1Typography
            {
                FontFamily = ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
                FontSize = "0.9375rem",
                FontWeight = "400",
                LineHeight = "1.7"
            },
            Button = new ButtonTypography
            {
                FontFamily = ["'Plus Jakarta Sans'", "Inter", "sans-serif"],
                FontSize = "0.875rem",
                FontWeight = "600",
                TextTransform = "none",
                LetterSpacing = "-0.01em"
            }
        },
        
        LayoutProperties = new LayoutProperties
        {
            DefaultBorderRadius = "12px",
            DrawerWidthLeft = "280px",
            AppbarHeight = "56px"
        }
    };
}
