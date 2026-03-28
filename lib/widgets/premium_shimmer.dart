import 'package:flutter/material.dart';

class PremiumShimmer extends StatefulWidget {
  const PremiumShimmer({super.key, this.width, this.height, this.borderRadius});

  final double? width;
  final double? height;
  final BorderRadius? borderRadius;

  @override
  State<PremiumShimmer> createState() => _PremiumShimmerState();
}

class _PremiumShimmerState extends State<PremiumShimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.width ?? double.infinity,
          height: widget.height ?? 24,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius ?? BorderRadius.circular(8),
            gradient: LinearGradient(
              begin: const Alignment(-2, -0.5),
              end: const Alignment(2, 0.5),
              colors: [
                Colors.white.withAlpha(10),
                Colors.white.withAlpha(40),
                Colors.white.withAlpha(10),
              ],
              stops: const [0.0, 0.5, 1.0],
              transform: _TranslateGradient(_controller.value),
            ),
          ),
        );
      },
    );
  }
}

class _TranslateGradient extends GradientTransform {
  const _TranslateGradient(this.value);
  final double value;

  @override
  Matrix4? transform(Rect bounds, {TextDirection? textDirection}) {
    final shift = (value * 3.0) - 1.5;
    return Matrix4.translationValues(bounds.width * shift, 0.0, 0.0);
  }
}
