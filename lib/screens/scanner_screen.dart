import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../services/api_service.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.noDuplicates,
    facing: CameraFacing.back,
  );

  bool _isHandlingDetection = false;
  bool _isSubmitting = false;
  String? _lastScannedBarcode;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_isHandlingDetection || _isSubmitting) {
      return;
    }

    String? barcodeValue;
    for (final barcode in capture.barcodes) {
      final rawValue = barcode.rawValue?.trim();
      if (rawValue != null && rawValue.isNotEmpty) {
        barcodeValue = rawValue;
        break;
      }
    }

    if (barcodeValue == null) {
      return;
    }

    _isHandlingDetection = true;
    await _controller.stop();

    try {
      final quantity = await _showQuantitySheet(barcodeValue);
      if (!mounted || quantity == null) {
        return;
      }

      setState(() => _isSubmitting = true);
      _lastScannedBarcode = barcodeValue;
      await ApiService().updateInventory(barcodeValue, quantity);

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Inventory updated for $barcodeValue (+$quantity).'),
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Inventory update failed: $error')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
        await _controller.start();
      }
      _isHandlingDetection = false;
    }
  }

  Future<int?> _showQuantitySheet(String barcode) async {
    final quantityController = TextEditingController(text: '1');

    final result = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (context) {
        String? errorText;

        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(
                24,
                20,
                24,
                MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: const Color(0xFF334155),
                        borderRadius: BorderRadius.circular(999),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Quantity to Add',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Barcode: $barcode',
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 18),
                  TextField(
                    controller: quantityController,
                    keyboardType: TextInputType.number,
                    autofocus: true,
                    decoration: InputDecoration(
                      labelText: 'Units',
                      errorText: errorText,
                    ),
                  ),
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        final quantity = int.tryParse(
                          quantityController.text.trim(),
                        );
                        if (quantity == null || quantity <= 0) {
                          setModalState(() {
                            errorText = 'Enter a valid quantity above zero.';
                          });
                          return;
                        }

                        Navigator.of(context).pop(quantity);
                      },
                      child: const Text('Confirm'),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );

    quantityController.dispose();
    return result;
  }

  Future<void> _handleManualEntry() async {
    final barcodeController = TextEditingController(text: _lastScannedBarcode);
    final quantityController = TextEditingController(text: '1');
    String? barcodeError;
    String? quantityError;

    final payload = await showModalBottomSheet<_ManualInventoryEntry>(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(
                24,
                20,
                24,
                MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: const Color(0xFF334155),
                        borderRadius: BorderRadius.circular(999),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Manual Inventory Update',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 18),
                  TextField(
                    controller: barcodeController,
                    autofocus: true,
                    decoration: InputDecoration(
                      labelText: 'Barcode',
                      errorText: barcodeError,
                    ),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: quantityController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Quantity',
                      errorText: quantityError,
                    ),
                  ),
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        final barcode = barcodeController.text.trim();
                        final quantity = int.tryParse(
                          quantityController.text.trim(),
                        );

                        setModalState(() {
                          barcodeError = barcode.isEmpty
                              ? 'Barcode is required.'
                              : null;
                          quantityError = quantity == null || quantity <= 0
                              ? 'Enter a valid quantity.'
                              : null;
                        });

                        if (barcodeError != null || quantityError != null) {
                          return;
                        }

                        Navigator.of(context).pop(
                          _ManualInventoryEntry(
                            barcode: barcode,
                            quantity: quantity!,
                          ),
                        );
                      },
                      child: const Text('Update Inventory'),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );

    barcodeController.dispose();
    quantityController.dispose();

    if (!mounted || payload == null) {
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      _lastScannedBarcode = payload.barcode;
      await ApiService().updateInventory(payload.barcode, payload.quantity);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Inventory updated for ${payload.barcode} (+${payload.quantity}).',
          ),
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Inventory update failed: $error')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _restartScanner() async {
    try {
      await _controller.start();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Unable to restart scanner: $error')),
        );
      }
    }
  }

  String _scannerErrorMessage(MobileScannerException error) {
    switch (error.errorCode) {
      case MobileScannerErrorCode.permissionDenied:
        return 'Camera access is required for live barcode scanning. You can retry after granting permission, or use manual entry below.';
      case MobileScannerErrorCode.unsupported:
        return 'This device does not support barcode scanning. Use manual inventory entry instead.';
      default:
        return error.errorDetails?.message ?? error.errorCode.message;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          ValueListenableBuilder<MobileScannerState>(
            valueListenable: _controller,
            builder: (context, scannerState, _) {
              return MobileScanner(
                controller: _controller,
                fit: BoxFit.cover,
                onDetect: _onDetect,
                errorBuilder: (context, error) {
                  return _ScannerFailureView(
                    message: _scannerErrorMessage(error),
                    onRetry: _restartScanner,
                    onManualEntry: _handleManualEntry,
                    isPermissionError:
                        error.errorCode ==
                        MobileScannerErrorCode.permissionDenied,
                  );
                },
                placeholderBuilder: (context) {
                  return const ColoredBox(
                    color: Color(0xFF0F172A),
                    child: Center(
                      child: CircularProgressIndicator(
                        color: Color(0xFF2563EB),
                      ),
                    ),
                  );
                },
                overlayBuilder: (context, constraints) {
                  if (!scannerState.hasCameraPermission &&
                      scannerState.error?.errorCode ==
                          MobileScannerErrorCode.permissionDenied) {
                    return const SizedBox.shrink();
                  }
                  return const SizedBox.shrink();
                },
              );
            },
          ),
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  const Color(0xCC0F172A),
                  Colors.transparent,
                  const Color(0xE60F172A),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                stops: const [0.0, 0.45, 1.0],
              ),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Native Scanner',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Scan a barcode to add stock instantly into your ONDC inventory.',
                    style: TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 15,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 18),
                  ValueListenableBuilder<MobileScannerState>(
                    valueListenable: _controller,
                    builder: (context, scannerState, _) {
                      final torchAvailable =
                          scannerState.torchState != TorchState.unavailable;
                      final torchOn = scannerState.torchState == TorchState.on;

                      return Row(
                        children: [
                          _ActionChip(
                            label: torchOn ? 'Torch On' : 'Torch Off',
                            icon: torchOn
                                ? Icons.flash_on_rounded
                                : Icons.flash_off_rounded,
                            enabled: torchAvailable,
                            onTap: torchAvailable
                                ? () => _controller.toggleTorch()
                                : null,
                          ),
                          const SizedBox(width: 12),
                          _ActionChip(
                            label: 'Manual Entry',
                            icon: Icons.keyboard_alt_rounded,
                            onTap: _handleManualEntry,
                          ),
                        ],
                      );
                    },
                  ),
                  const Spacer(),
                  Center(
                    child: Container(
                      width: 270,
                      height: 270,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(28),
                        border: Border.all(
                          color: const Color(0xFF60A5FA),
                          width: 3,
                        ),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x332563EB),
                            blurRadius: 28,
                            spreadRadius: 8,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: const Color(0xCC111827),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFF1E293B)),
                    ),
                    child: const Row(
                      children: [
                        Icon(
                          Icons.inventory_2_outlined,
                          color: Color(0xFF38BDF8),
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Align the product barcode inside the frame. The camera will pause while you confirm quantity.',
                            style: TextStyle(
                              color: Color(0xFFCBD5E1),
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_isSubmitting)
            Container(
              color: const Color(0xAA0F172A),
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircularProgressIndicator(color: Color(0xFF2563EB)),
                    SizedBox(height: 16),
                    Text(
                      'Updating inventory...',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({
    required this.label,
    required this.icon,
    this.onTap,
    this.enabled = true,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: enabled ? const Color(0xCC111827) : const Color(0x80111827),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                color: enabled
                    ? const Color(0xFFCBD5E1)
                    : const Color(0xFF64748B),
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: enabled
                      ? const Color(0xFFCBD5E1)
                      : const Color(0xFF64748B),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ScannerFailureView extends StatelessWidget {
  const _ScannerFailureView({
    required this.message,
    required this.onRetry,
    required this.onManualEntry,
    required this.isPermissionError,
  });

  final String message;
  final Future<void> Function() onRetry;
  final Future<void> Function() onManualEntry;
  final bool isPermissionError;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: const Color(0xFF0F172A),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Container(
            constraints: const BoxConstraints(maxWidth: 420),
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: const Color(0xFF111827),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xFF1E293B)),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  isPermissionError
                      ? Icons.no_photography_outlined
                      : Icons.error_outline_rounded,
                  color: const Color(0xFF60A5FA),
                  size: 34,
                ),
                const SizedBox(height: 16),
                Text(
                  isPermissionError
                      ? 'Camera Access Needed'
                      : 'Scanner Unavailable',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  message,
                  style: const TextStyle(
                    color: Color(0xFFCBD5E1),
                    height: 1.45,
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: onRetry,
                        child: const Text('Retry Camera'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton(
                        onPressed: onManualEntry,
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: Color(0xFF334155)),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(18),
                          ),
                        ),
                        child: const Text('Manual Entry'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ManualInventoryEntry {
  const _ManualInventoryEntry({required this.barcode, required this.quantity});

  final String barcode;
  final int quantity;
}
