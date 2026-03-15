import 'package:flutter/material.dart';

import '../services/api_service.dart';

class ProductsScreen extends StatefulWidget {
  const ProductsScreen({super.key});

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  final _searchController = TextEditingController();
  late Future<List<Map<String, dynamic>>> _productsFuture;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _productsFuture = ApiService().getCatalog();
  }

  Future<void> _refresh() async {
    setState(() {
      _productsFuture = ApiService().getCatalog(search: _searchQuery);
    });
    await _productsFuture;
  }

  void _onSearchChanged(String query) {
    _searchQuery = query.trim();
    _refresh();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Products',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Your complete catalog synced from WhatsApp and the dashboard.',
                    style: TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 15,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _searchController,
                    onChanged: _onSearchChanged,
                    decoration: InputDecoration(
                      hintText: 'Search products...',
                      prefixIcon: const Icon(Icons.search, size: 20),
                      suffixIcon: _searchQuery.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.close, size: 18),
                              onPressed: () {
                                _searchController.clear();
                                _onSearchChanged('');
                              },
                            )
                          : null,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: FutureBuilder<List<Map<String, dynamic>>>(
                future: _productsFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return _buildLoading();
                  }
                  if (snapshot.hasError) {
                    return _buildError(snapshot.error);
                  }
                  final products = snapshot.data ?? [];
                  if (products.isEmpty) {
                    return _buildEmpty();
                  }
                  return RefreshIndicator(
                    color: const Color(0xFF2563EB),
                    onRefresh: _refresh,
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
                      physics: const AlwaysScrollableScrollPhysics(),
                      itemCount: products.length,
                      separatorBuilder: (_, index) => const SizedBox(height: 10),
                      itemBuilder: (context, index) {
                        return _ProductCard(
                          product: products[index],
                          onTap: () => _showProductDetail(products[index]),
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddProduct,
        backgroundColor: const Color(0xFF2563EB),
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  void _showProductDetail(Map<String, dynamic> product) {
    final itemId = product['id']?.toString() ?? '';
    final nameCtrl = TextEditingController(text: product['name'] ?? '');
    final priceCtrl = TextEditingController(
      text: '${product['selling_price'] ?? product['price'] ?? 0}',
    );
    final qtyCtrl = TextEditingController(text: '${product['quantity'] ?? 0}');
    final categoryCtrl = TextEditingController(text: product['category'] ?? '');
    String? errorText;
    bool isSaving = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (ctx) {
        return StatefulBuilder(builder: (ctx, setModalState) {
          return Padding(
            padding: EdgeInsets.fromLTRB(
              24, 20, 24, MediaQuery.of(ctx).viewInsets.bottom + 24,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40, height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFF334155),
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    const Expanded(
                      child: Text('Edit Product',
                        style: TextStyle(
                          color: Colors.white, fontSize: 24, fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    if (itemId.isNotEmpty)
                      IconButton(
                        onPressed: isSaving ? null : () async {
                          final confirm = await showDialog<bool>(
                            context: ctx,
                            builder: (dCtx) => AlertDialog(
                              backgroundColor: const Color(0xFF111827),
                              title: const Text('Delete product?',
                                style: TextStyle(color: Colors.white),
                              ),
                              content: Text(
                                'This will remove "${nameCtrl.text}" from your catalog.',
                                style: const TextStyle(color: Color(0xFFCBD5E1)),
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(dCtx, false),
                                  child: const Text('Cancel'),
                                ),
                                TextButton(
                                  onPressed: () => Navigator.pop(dCtx, true),
                                  child: const Text('Delete',
                                    style: TextStyle(color: Color(0xFFEF4444)),
                                  ),
                                ),
                              ],
                            ),
                          );
                          if (confirm == true) {
                            try {
                              await ApiService().deleteProduct(itemId);
                              if (ctx.mounted) Navigator.pop(ctx);
                              _refresh();
                            } catch (e) {
                              setModalState(() => errorText = '$e');
                            }
                          }
                        },
                        icon: const Icon(Icons.delete_outline,
                          color: Color(0xFFEF4444), size: 22,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(labelText: 'Product name'),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: priceCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Price (₹)'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: qtyCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Quantity'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: categoryCtrl,
                  decoration: const InputDecoration(labelText: 'Category'),
                ),
                if (errorText != null) ...[
                  const SizedBox(height: 12),
                  Text(errorText!,
                    style: const TextStyle(color: Color(0xFFFCA5A5), fontSize: 13),
                  ),
                ],
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: isSaving ? null : () async {
                      final name = nameCtrl.text.trim();
                      final price = double.tryParse(priceCtrl.text.trim());
                      final qty = int.tryParse(qtyCtrl.text.trim());

                      if (name.isEmpty || price == null || qty == null) {
                        setModalState(() => errorText = 'All fields are required.');
                        return;
                      }

                      setModalState(() { isSaving = true; errorText = null; });
                      try {
                        if (itemId.isNotEmpty) {
                          await ApiService().updateProduct(itemId, {
                            'name': name,
                            'selling_price': price,
                            'quantity': qty,
                            'category': categoryCtrl.text.trim(),
                          });
                        } else {
                          await ApiService().addProduct(
                            name: name, price: price, quantity: qty,
                            category: categoryCtrl.text.trim(),
                          );
                        }
                        if (ctx.mounted) Navigator.pop(ctx);
                        _refresh();
                      } catch (e) {
                        setModalState(() { isSaving = false; errorText = '$e'; });
                      }
                    },
                    child: isSaving
                        ? const SizedBox(
                            width: 22, height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.2, color: Colors.white,
                            ),
                          )
                        : Text(itemId.isNotEmpty ? 'Save Changes' : 'Create'),
                  ),
                ),
              ],
            ),
          );
        });
      },
    );
  }

  void _showAddProduct() {
    final nameCtrl = TextEditingController();
    final priceCtrl = TextEditingController();
    final qtyCtrl = TextEditingController(text: '1');
    final categoryCtrl = TextEditingController();
    String? errorText;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (ctx) {
        return StatefulBuilder(builder: (ctx, setModalState) {
          return Padding(
            padding: EdgeInsets.fromLTRB(
              24, 20, 24, MediaQuery.of(ctx).viewInsets.bottom + 24,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40, height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFF334155),
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                const Text('Add Product',
                  style: TextStyle(
                    color: Colors.white, fontSize: 24, fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 18),
                TextField(
                  controller: nameCtrl,
                  autofocus: true,
                  decoration: const InputDecoration(labelText: 'Product name'),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: priceCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Price (₹)'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: qtyCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Quantity'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: categoryCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Category (optional)',
                  ),
                ),
                if (errorText != null) ...[
                  const SizedBox(height: 12),
                  Text(errorText!,
                    style: const TextStyle(color: Color(0xFFFCA5A5), fontSize: 13),
                  ),
                ],
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () async {
                      final name = nameCtrl.text.trim();
                      final price = double.tryParse(priceCtrl.text.trim());
                      final qty = int.tryParse(qtyCtrl.text.trim());

                      if (name.isEmpty || price == null || qty == null) {
                        setModalState(() => errorText = 'Name, price, and quantity are required.');
                        return;
                      }

                      try {
                        await ApiService().addProduct(
                          name: name,
                          price: price,
                          quantity: qty,
                          category: categoryCtrl.text.trim(),
                        );
                        if (ctx.mounted) Navigator.pop(ctx);
                        _refresh();
                      } catch (e) {
                        setModalState(() => errorText = '$e');
                      }
                    },
                    child: const Text('Add to Catalog'),
                  ),
                ),
              ],
            ),
          );
        });
      },
    );
  }

  Widget _buildLoading() {
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      children: List.generate(4, (_) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Container(
          height: 90,
          decoration: BoxDecoration(
            color: const Color(0xFF111827),
            borderRadius: BorderRadius.circular(20),
          ),
        ),
      )),
    );
  }

  Widget _buildError(Object? error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFF97316), size: 48),
            const SizedBox(height: 16),
            Text(
              '$error',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFFCBD5E1), height: 1.4),
            ),
            const SizedBox(height: 18),
            ElevatedButton(onPressed: _refresh, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFF111827),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(Icons.inventory_2_outlined,
                  color: Color(0xFF64748B), size: 40),
            ),
            const SizedBox(height: 20),
            const Text(
              'No products yet',
              style: TextStyle(
                color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _searchQuery.isNotEmpty
                  ? 'No products match "$_searchQuery".'
                  : 'Add products via WhatsApp or tap + below.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF94A3B8), height: 1.4),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({required this.product, required this.onTap});

  final Map<String, dynamic> product;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final name = product['name'] ?? 'Unknown';
    final price = product['selling_price'] ?? product['price'] ?? 0;
    final qty = product['quantity'] ?? 0;
    final category = product['category'] ?? '';

    final isLowStock = qty is int && qty <= 5;

    return Material(
      color: const Color(0xFF111827),
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isLowStock
                  ? const Color(0xFFF97316).withAlpha(60)
                  : const Color(0xFF1E293B),
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 50, height: 50,
                decoration: BoxDecoration(
                  color: isLowStock
                      ? const Color(0xFFF97316).withAlpha(30)
                      : const Color(0xFF2563EB).withAlpha(30),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(
                  isLowStock ? Icons.warning_amber_rounded : Icons.inventory_2,
                  color: isLowStock
                      ? const Color(0xFFF97316)
                      : const Color(0xFF60A5FA),
                  size: 22,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text('₹$price',
                          style: const TextStyle(
                            color: Color(0xFF22C55E),
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                        if (category.isNotEmpty) ...[
                          const Text(' · ',
                            style: TextStyle(color: Color(0xFF64748B)),
                          ),
                          Flexible(
                            child: Text(category,
                              style: const TextStyle(
                                color: Color(0xFF94A3B8), fontSize: 13,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Column(
                children: [
                  Text('$qty',
                    style: TextStyle(
                      color: isLowStock
                          ? const Color(0xFFF97316)
                          : Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    isLowStock ? 'LOW' : 'qty',
                    style: TextStyle(
                      color: isLowStock
                          ? const Color(0xFFF97316)
                          : const Color(0xFF64748B),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
