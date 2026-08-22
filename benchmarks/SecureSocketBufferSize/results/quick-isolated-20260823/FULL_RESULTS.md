<a id="full-benchmark-results"></a>
# Full benchmark results

[Back to the benchmark report](REPORT.md)

Values are medians across valid repetitions unless labeled as a minimum, maximum, or coefficient of variation (CV). These tables expose the absolute values behind the normalized comparisons in the main report. Per-repetition measurements remain available in `cell_results.csv`.

## 8 KiB TLS/plaintext absolute results

<a id="absolute-8-kib-qps"></a>
### QPS and variability

| Target | Role | Path | TLS | Payload | QPS median | QPS min | QPS max | CV |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Dart | server | io | no | 1 KiB | 46,693 | 46,624 | 47,278 | 0.6% |
| Dart | server | io | yes | 1 KiB | 11,599 | 11,399 | 11,728 | 1.2% |
| Node.js | server | io | no | 1 KiB | 49,496 | 48,857 | 49,629 | 0.7% |
| Node.js | server | io | yes | 1 KiB | 41,178 | 40,541 | 41,669 | 1.1% |
| Go | server | io | no | 1 KiB | 50,358 | 49,983 | 50,729 | 0.6% |
| Go | server | io | yes | 1 KiB | 44,070 | 43,158 | 44,876 | 1.6% |
| Dart | server | io | no | 16 KiB | 37,795 | 36,866 | 38,230 | 1.5% |
| Dart | server | io | yes | 16 KiB | 2,634 | 2,622 | 2,652 | 0.5% |
| Node.js | server | io | no | 16 KiB | 41,394 | 40,666 | 41,726 | 1.1% |
| Node.js | server | io | yes | 16 KiB | 25,506 | 25,306 | 25,544 | 0.4% |
| Go | server | io | no | 16 KiB | 41,053 | 39,912 | 42,694 | 2.8% |
| Go | server | io | yes | 16 KiB | 23,560 | 23,500 | 23,944 | 0.8% |
| Dart | server | io | no | 64 KiB | 12,122 | 12,051 | 12,280 | 0.8% |
| Dart | server | io | yes | 64 KiB | 659 | 637 | 660 | 1.6% |
| Node.js | server | io | no | 64 KiB | 20,755 | 19,900 | 20,909 | 2.2% |
| Node.js | server | io | yes | 64 KiB | 7,002 | 6,893 | 7,063 | 1.0% |
| Go | server | io | no | 64 KiB | 20,546 | 20,463 | 22,322 | 4.1% |
| Go | server | io | yes | 64 KiB | 5,934 | 5,495 | 5,975 | 3.8% |
| Dart | server | io | no | 1 MiB | 948 | 933 | 1,000 | 3.0% |
| Dart | server | io | yes | 1 MiB | 41 | 41 | 41 | 0.7% |
| Node.js | server | io | no | 1 MiB | 1,495 | 1,230 | 1,651 | 11.9% |
| Node.js | server | io | yes | 1 MiB | 492 | 477 | 492 | 1.4% |
| Go | server | io | no | 1 MiB | 4,350 | 4,268 | 4,422 | 1.4% |
| Go | server | io | yes | 1 MiB | 329 | 325 | 685 | 37.8% |
| Dart | server | http | no | 1 KiB | 13,561 | 13,259 | 13,742 | 1.5% |
| Dart | server | http | yes | 1 KiB | 6,605 | 6,519 | 6,630 | 0.7% |
| Node.js | server | http | no | 1 KiB | 22,426 | 21,855 | 22,602 | 1.4% |
| Node.js | server | http | yes | 1 KiB | 16,614 | 16,548 | 16,940 | 1.0% |
| Go | server | http | no | 1 KiB | 47,768 | 47,381 | 47,870 | 0.4% |
| Go | server | http | yes | 1 KiB | 40,208 | 39,491 | 40,596 | 1.1% |
| Dart | server | http | no | 16 KiB | 11,592 | 11,588 | 11,602 | 0.0% |
| Dart | server | http | yes | 16 KiB | 2,576 | 2,494 | 2,597 | 1.7% |
| Node.js | server | http | no | 16 KiB | 16,637 | 16,058 | 16,867 | 2.1% |
| Node.js | server | http | yes | 16 KiB | 11,163 | 11,011 | 11,369 | 1.3% |
| Go | server | http | no | 16 KiB | 20,924 | 20,781 | 20,999 | 0.4% |
| Go | server | http | yes | 16 KiB | 16,008 | 15,962 | 16,382 | 1.2% |
| Dart | server | http | no | 64 KiB | 8,655 | 8,645 | 8,716 | 0.4% |
| Dart | server | http | yes | 64 KiB | 828 | 825 | 836 | 0.6% |
| Node.js | server | http | no | 64 KiB | 10,580 | 9,760 | 11,101 | 5.3% |
| Node.js | server | http | yes | 64 KiB | 7,192 | 6,893 | 7,223 | 2.1% |
| Go | server | http | no | 64 KiB | 14,906 | 14,888 | 14,917 | 0.1% |
| Go | server | http | yes | 64 KiB | 8,803 | 8,566 | 8,855 | 1.4% |
| Dart | server | http | no | 1 MiB | 585 | 538 | 621 | 5.8% |
| Dart | server | http | yes | 1 MiB | 63 | 60 | 63 | 2.3% |
| Node.js | server | http | no | 1 MiB | 1,919 | 1,916 | 2,058 | 3.4% |
| Node.js | server | http | yes | 1 MiB | 785 | 776 | 804 | 1.5% |
| Go | server | http | no | 1 MiB | 2,487 | 2,414 | 2,587 | 2.8% |
| Go | server | http | yes | 1 MiB | 905 | 899 | 951 | 2.5% |
| Dart | client | io | no | 1 KiB | 70,332 | 70,219 | 70,501 | 0.2% |
| Dart | client | io | yes | 1 KiB | 21,715 | 21,586 | 21,843 | 0.5% |
| Node.js | client | io | no | 1 KiB | 104,253 | 102,789 | 105,423 | 1.0% |
| Node.js | client | io | yes | 1 KiB | 68,988 | 68,793 | 70,660 | 1.2% |
| Go | client | io | no | 1 KiB | 91,240 | 88,226 | 91,256 | 1.6% |
| Go | client | io | yes | 1 KiB | 118,581 | 118,459 | 120,917 | 0.9% |
| Dart | client | io | no | 16 KiB | 55,477 | 55,318 | 55,791 | 0.4% |
| Dart | client | io | yes | 16 KiB | 2,698 | 2,689 | 2,748 | 1.0% |
| Node.js | client | io | no | 16 KiB | 55,131 | 54,076 | 56,250 | 1.6% |
| Node.js | client | io | yes | 16 KiB | 32,387 | 31,889 | 32,407 | 0.7% |
| Go | client | io | no | 16 KiB | 82,411 | 81,469 | 83,257 | 0.9% |
| Go | client | io | yes | 16 KiB | 63,097 | 60,519 | 63,244 | 2.0% |
| Dart | client | io | no | 64 KiB | 13,609 | 13,339 | 13,861 | 1.6% |
| Dart | client | io | yes | 64 KiB | 926 | 918 | 937 | 0.8% |
| Node.js | client | io | no | 64 KiB | 16,743 | 16,146 | 16,833 | 1.8% |
| Node.js | client | io | yes | 64 KiB | 11,988 | 11,881 | 12,015 | 0.5% |
| Go | client | io | no | 64 KiB | 50,826 | 49,214 | 50,955 | 1.6% |
| Go | client | io | yes | 64 KiB | 15,295 | 13,960 | 15,542 | 4.7% |
| Dart | client | io | no | 1 MiB | 1,012 | 997 | 1,030 | 1.3% |
| Dart | client | io | yes | 1 MiB | 95 | 95 | 97 | 0.7% |
| Node.js | client | io | no | 1 MiB | 1,663 | 1,612 | 1,667 | 1.5% |
| Node.js | client | io | yes | 1 MiB | 1,021 | 1,010 | 1,039 | 1.1% |
| Go | client | io | no | 1 MiB | 5,443 | 4,012 | 5,487 | 13.8% |
| Go | client | io | yes | 1 MiB | 814 | 747 | 927 | 8.9% |
| Dart | client | http | no | 1 KiB | 8,717 | 8,418 | 8,723 | 1.7% |
| Dart | client | http | yes | 1 KiB | 5,396 | 5,343 | 5,475 | 1.0% |
| Node.js | client | http | no | 1 KiB | 13,924 | 13,772 | 14,102 | 1.0% |
| Node.js | client | http | yes | 1 KiB | 9,831 | 9,605 | 9,894 | 1.3% |
| Go | client | http | no | 1 KiB | 35,080 | 34,740 | 35,495 | 0.9% |
| Go | client | http | yes | 1 KiB | 30,407 | 29,903 | 30,705 | 1.1% |
| Dart | client | http | no | 16 KiB | 8,338 | 8,311 | 8,373 | 0.3% |
| Dart | client | http | yes | 16 KiB | 2,122 | 2,071 | 2,147 | 1.5% |
| Node.js | client | http | no | 16 KiB | 9,719 | 9,535 | 10,836 | 5.7% |
| Node.js | client | http | yes | 16 KiB | 7,833 | 7,756 | 7,934 | 0.9% |
| Go | client | http | no | 16 KiB | 17,332 | 17,308 | 17,577 | 0.7% |
| Go | client | http | yes | 16 KiB | 14,443 | 14,134 | 14,785 | 1.8% |
| Dart | client | http | no | 64 KiB | 7,116 | 6,591 | 7,297 | 4.3% |
| Dart | client | http | yes | 64 KiB | 678 | 654 | 683 | 1.9% |
| Node.js | client | http | no | 64 KiB | 9,201 | 6,225 | 9,449 | 17.7% |
| Node.js | client | http | yes | 64 KiB | 5,011 | 4,965 | 5,012 | 0.4% |
| Go | client | http | no | 64 KiB | 11,793 | 11,779 | 11,899 | 0.5% |
| Go | client | http | yes | 64 KiB | 8,168 | 7,835 | 8,236 | 2.2% |
| Dart | client | http | no | 1 MiB | 652 | 646 | 677 | 2.0% |
| Dart | client | http | yes | 1 MiB | 50 | 49 | 51 | 1.6% |
| Node.js | client | http | no | 1 MiB | 1,123 | 1,105 | 1,139 | 1.2% |
| Node.js | client | http | yes | 1 MiB | 583 | 579 | 603 | 1.8% |
| Go | client | http | no | 1 MiB | 1,742 | 1,719 | 1,795 | 1.8% |
| Go | client | http | yes | 1 MiB | 832 | 823 | 834 | 0.6% |

<a id="absolute-8-kib-target-cpu"></a>
### Target CPU

| Target | Role | Path | TLS | Payload | CPU ns/op | User ns/op | System ns/op | Target CPU |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Dart | server | io | no | 1 KiB | 13,294 | 4,537 | 8,757 | 60.0% |
| Dart | server | io | yes | 1 KiB | 86,180 | 33,294 | 52,886 | 96.8% |
| Node.js | server | io | no | 1 KiB | 10,340 | 3,610 | 6,728 | 48.9% |
| Node.js | server | io | yes | 1 KiB | 19,103 | 8,827 | 10,222 | 75.8% |
| Go | server | io | no | 1 KiB | 10,113 | 1,522 | 8,590 | 49.5% |
| Go | server | io | yes | 1 KiB | 14,721 | 3,069 | 11,653 | 62.4% |
| Dart | server | io | no | 16 KiB | 17,825 | 5,841 | 12,283 | 64.9% |
| Dart | server | io | yes | 16 KiB | 379,554 | 141,251 | 238,381 | 97.4% |
| Node.js | server | io | no | 16 KiB | 16,094 | 5,137 | 10,984 | 64.0% |
| Node.js | server | io | yes | 16 KiB | 35,882 | 20,655 | 15,923 | 88.9% |
| Go | server | io | no | 16 KiB | 12,500 | 1,777 | 10,722 | 49.7% |
| Go | server | io | yes | 16 KiB | 29,615 | 9,728 | 19,448 | 67.7% |
| Dart | server | io | no | 64 KiB | 79,593 | 27,581 | 52,012 | 93.8% |
| Dart | server | io | yes | 64 KiB | 1,516,569 | 582,634 | 958,033 | 97.4% |
| Node.js | server | io | no | 64 KiB | 40,725 | 10,699 | 30,026 | 81.8% |
| Node.js | server | io | yes | 64 KiB | 131,070 | 79,260 | 51,476 | 89.0% |
| Go | server | io | no | 64 KiB | 29,355 | 2,966 | 26,293 | 59.4% |
| Go | server | io | yes | 64 KiB | 121,058 | 39,603 | 81,455 | 70.4% |
| Dart | server | io | no | 1 MiB | 1,047,243 | 222,185 | 826,034 | 96.4% |
| Dart | server | io | yes | 1 MiB | 24,020,563 | 9,086,326 | 15,140,406 | 96.9% |
| Node.js | server | io | no | 1 MiB | 660,701 | 163,110 | 497,591 | 96.2% |
| Node.js | server | io | yes | 1 MiB | 2,028,416 | 1,266,584 | 752,266 | 96.5% |
| Go | server | io | no | 1 MiB | 129,896 | 10,461 | 119,614 | 55.6% |
| Go | server | io | yes | 1 MiB | 1,052,331 | 542,808 | 503,826 | 33.9% |
| Dart | server | http | no | 1 KiB | 73,416 | 30,272 | 43,021 | 96.2% |
| Dart | server | http | yes | 1 KiB | 151,245 | 73,227 | 78,643 | 96.9% |
| Node.js | server | http | no | 1 KiB | 44,093 | 23,845 | 20,357 | 95.7% |
| Node.js | server | http | yes | 1 KiB | 59,779 | 35,640 | 23,965 | 96.1% |
| Go | server | http | no | 1 KiB | 20,172 | 9,139 | 10,990 | 93.4% |
| Go | server | http | yes | 1 KiB | 24,201 | 11,857 | 12,343 | 94.3% |
| Dart | server | http | no | 16 KiB | 85,607 | 34,332 | 51,318 | 96.6% |
| Dart | server | http | yes | 16 KiB | 388,160 | 172,597 | 215,564 | 96.8% |
| Node.js | server | http | no | 16 KiB | 58,518 | 28,310 | 30,209 | 94.5% |
| Node.js | server | http | yes | 16 KiB | 89,254 | 53,361 | 35,893 | 96.1% |
| Go | server | http | no | 16 KiB | 45,789 | 15,722 | 30,266 | 93.1% |
| Go | server | http | yes | 16 KiB | 60,962 | 23,822 | 35,506 | 94.4% |
| Dart | server | http | no | 64 KiB | 115,163 | 38,425 | 76,738 | 97.2% |
| Dart | server | http | yes | 64 KiB | 1,207,679 | 527,495 | 679,069 | 96.8% |
| Node.js | server | http | no | 64 KiB | 93,360 | 38,441 | 55,382 | 95.7% |
| Node.js | server | http | yes | 64 KiB | 138,883 | 90,050 | 49,132 | 96.9% |
| Go | server | http | no | 64 KiB | 64,423 | 19,688 | 44,742 | 92.9% |
| Go | server | http | yes | 64 KiB | 113,440 | 46,240 | 66,918 | 96.4% |
| Dart | server | http | no | 1 MiB | 1,701,312 | 392,158 | 1,309,155 | 96.6% |
| Dart | server | http | yes | 1 MiB | 15,816,068 | 6,950,219 | 8,904,754 | 96.7% |
| Node.js | server | http | no | 1 MiB | 519,291 | 241,285 | 273,775 | 96.5% |
| Node.js | server | http | yes | 1 MiB | 1,272,987 | 948,276 | 314,293 | 97.1% |
| Go | server | http | no | 1 MiB | 401,542 | 70,880 | 327,686 | 97.1% |
| Go | server | http | yes | 1 MiB | 1,102,878 | 455,722 | 650,690 | 96.6% |
| Dart | client | io | no | 1 KiB | 14,270 | 3,558 | 10,716 | 96.9% |
| Dart | client | io | yes | 1 KiB | 46,140 | 18,164 | 28,088 | 97.0% |
| Node.js | client | io | no | 1 KiB | 9,702 | 2,593 | 7,047 | 95.9% |
| Node.js | client | io | yes | 1 KiB | 14,362 | 6,846 | 7,587 | 95.5% |
| Go | client | io | no | 1 KiB | 10,691 | 1,641 | 9,100 | 93.7% |
| Go | client | io | yes | 1 KiB | 8,383 | 1,973 | 6,391 | 95.9% |
| Dart | client | io | no | 16 KiB | 18,073 | 4,907 | 13,166 | 96.6% |
| Dart | client | io | yes | 16 KiB | 370,868 | 143,649 | 224,841 | 96.9% |
| Node.js | client | io | no | 16 KiB | 18,317 | 6,037 | 12,100 | 96.6% |
| Node.js | client | io | yes | 16 KiB | 29,028 | 19,711 | 9,218 | 89.6% |
| Go | client | io | no | 16 KiB | 11,973 | 1,481 | 10,492 | 95.2% |
| Go | client | io | yes | 16 KiB | 15,776 | 7,442 | 8,572 | 95.9% |
| Dart | client | io | no | 64 KiB | 73,411 | 18,990 | 55,418 | 97.4% |
| Dart | client | io | yes | 64 KiB | 1,079,325 | 434,914 | 643,939 | 97.3% |
| Node.js | client | io | no | 64 KiB | 59,916 | 16,222 | 43,774 | 97.1% |
| Node.js | client | io | yes | 64 KiB | 83,559 | 62,186 | 21,373 | 96.8% |
| Go | client | io | no | 64 KiB | 19,671 | 1,646 | 18,034 | 96.5% |
| Go | client | io | yes | 64 KiB | 63,496 | 28,728 | 33,814 | 93.5% |
| Dart | client | io | no | 1 MiB | 985,085 | 187,311 | 797,854 | 97.4% |
| Dart | client | io | yes | 1 MiB | 10,474,372 | 4,859,467 | 5,617,050 | 96.9% |
| Node.js | client | io | no | 1 MiB | 597,020 | 126,036 | 476,103 | 96.6% |
| Node.js | client | io | yes | 1 MiB | 978,947 | 734,460 | 227,375 | 96.8% |
| Go | client | io | no | 1 MiB | 183,085 | 3,172 | 179,913 | 96.8% |
| Go | client | io | yes | 1 MiB | 945,522 | 488,830 | 457,524 | 75.3% |
| Dart | client | http | no | 1 KiB | 114,859 | 55,082 | 62,192 | 96.9% |
| Dart | client | http | yes | 1 KiB | 185,514 | 92,664 | 93,008 | 96.9% |
| Node.js | client | http | no | 1 KiB | 72,039 | 46,769 | 25,234 | 97.3% |
| Node.js | client | http | yes | 1 KiB | 101,939 | 72,383 | 29,785 | 97.1% |
| Go | client | http | no | 1 KiB | 28,424 | 14,854 | 13,519 | 96.3% |
| Go | client | http | yes | 1 KiB | 32,836 | 17,553 | 15,025 | 96.3% |
| Dart | client | http | no | 16 KiB | 120,059 | 53,911 | 66,450 | 97.2% |
| Dart | client | http | yes | 16 KiB | 471,595 | 210,727 | 260,871 | 97.4% |
| Node.js | client | http | no | 16 KiB | 102,955 | 55,372 | 46,602 | 96.8% |
| Node.js | client | http | yes | 16 KiB | 127,868 | 90,192 | 37,810 | 97.4% |
| Go | client | http | no | 16 KiB | 57,723 | 23,895 | 33,842 | 96.6% |
| Go | client | http | yes | 16 KiB | 69,138 | 31,990 | 37,549 | 96.7% |
| Dart | client | http | no | 64 KiB | 140,600 | 61,120 | 79,481 | 96.9% |
| Dart | client | http | yes | 64 KiB | 1,475,736 | 637,410 | 835,766 | 96.8% |
| Node.js | client | http | no | 64 KiB | 108,901 | 60,531 | 50,852 | 97.3% |
| Node.js | client | http | yes | 64 KiB | 199,649 | 146,448 | 53,190 | 96.9% |
| Go | client | http | no | 64 KiB | 84,888 | 31,529 | 53,235 | 96.8% |
| Go | client | http | yes | 64 KiB | 122,373 | 59,172 | 64,427 | 96.8% |
| Dart | client | http | no | 1 MiB | 1,532,301 | 435,591 | 1,085,101 | 96.7% |
| Dart | client | http | yes | 1 MiB | 19,740,511 | 7,914,349 | 11,568,852 | 97.0% |
| Node.js | client | http | no | 1 MiB | 888,389 | 560,551 | 324,369 | 96.9% |
| Node.js | client | http | yes | 1 MiB | 1,715,061 | 1,391,590 | 323,471 | 96.8% |
| Go | client | http | no | 1 MiB | 572,701 | 127,294 | 445,445 | 96.7% |
| Go | client | http | yes | 1 MiB | 1,201,152 | 503,986 | 697,173 | 96.8% |

<a id="absolute-8-kib-latency"></a>
### Latency

| Target | Role | Path | TLS | Payload | Mean | p50 | p95 | p99 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Dart | server | io | no | 1 KiB | 139.4 µs | 138.8 µs | 165.9 µs | 190.9 µs |
| Dart | server | io | yes | 1 KiB | 269.4 µs | 260.9 µs | 319.2 µs | 383.3 µs |
| Node.js | server | io | no | 1 KiB | 118.5 µs | 114.3 µs | 147.9 µs | 171.0 µs |
| Node.js | server | io | yes | 1 KiB | 141.5 µs | 141.5 µs | 164.7 µs | 188.1 µs |
| Go | server | io | no | 1 KiB | 113.2 µs | 108.4 µs | 141.0 µs | 162.0 µs |
| Go | server | io | yes | 1 KiB | 123.9 µs | 122.8 µs | 150.8 µs | 171.2 µs |
| Dart | server | io | no | 16 KiB | 150.8 µs | 147.4 µs | 176.1 µs | 217.7 µs |
| Dart | server | io | yes | 16 KiB | 551.0 µs | 539.4 µs | 635.8 µs | 736.3 µs |
| Node.js | server | io | no | 16 KiB | 125.7 µs | 124.7 µs | 156.3 µs | 179.4 µs |
| Node.js | server | io | yes | 16 KiB | 170.0 µs | 168.0 µs | 195.2 µs | 222.3 µs |
| Go | server | io | no | 16 KiB | 117.7 µs | 113.8 µs | 146.0 µs | 166.3 µs |
| Go | server | io | yes | 16 KiB | 150.5 µs | 149.1 µs | 171.7 µs | 195.4 µs |
| Dart | server | io | no | 64 KiB | 177.3 µs | 172.5 µs | 220.3 µs | 260.5 µs |
| Dart | server | io | yes | 64 KiB | 1.67 ms | 1.65 ms | 1.84 ms | 1.98 ms |
| Node.js | server | io | no | 64 KiB | 160.8 µs | 150.6 µs | 191.1 µs | 235.7 µs |
| Node.js | server | io | yes | 64 KiB | 307.6 µs | 303.7 µs | 356.6 µs | 414.7 µs |
| Go | server | io | no | 64 KiB | 145.8 µs | 144.9 µs | 168.1 µs | 191.3 µs |
| Go | server | io | yes | 64 KiB | 195.5 µs | 191.1 µs | 247.5 µs | 285.5 µs |
| Dart | server | io | no | 1 MiB | 1.18 ms | 1.13 ms | 1.62 ms | 2.12 ms |
| Dart | server | io | yes | 1 MiB | 24.68 ms | 24.40 ms | 26.17 ms | 26.87 ms |
| Node.js | server | io | no | 1 MiB | 812.4 µs | 704.5 µs | 1.03 ms | 4.52 ms |
| Node.js | server | io | yes | 1 MiB | 2.22 ms | 2.23 ms | 2.47 ms | 2.70 ms |
| Go | server | io | no | 1 MiB | 271.0 µs | 261.4 µs | 313.4 µs | 448.7 µs |
| Go | server | io | yes | 1 MiB | 2.44 ms | 2.44 ms | 2.64 ms | 2.80 ms |
| Dart | server | http | no | 1 KiB | 206.9 µs | 203.3 µs | 248.2 µs | 324.4 µs |
| Dart | server | http | yes | 1 KiB | 329.8 µs | 321.6 µs | 394.4 µs | 473.9 µs |
| Node.js | server | http | no | 1 KiB | 188.4 µs | 184.4 µs | 225.4 µs | 262.6 µs |
| Node.js | server | http | yes | 1 KiB | 197.9 µs | 192.1 µs | 242.3 µs | 283.2 µs |
| Go | server | http | no | 1 KiB | 173.0 µs | 170.4 µs | 207.9 µs | 238.0 µs |
| Go | server | http | yes | 1 KiB | 179.2 µs | 176.3 µs | 216.2 µs | 247.5 µs |
| Dart | server | http | no | 16 KiB | 215.7 µs | 210.4 µs | 268.4 µs | 340.4 µs |
| Dart | server | http | yes | 16 KiB | 557.6 µs | 544.3 µs | 672.8 µs | 776.5 µs |
| Node.js | server | http | no | 16 KiB | 204.8 µs | 200.8 µs | 253.6 µs | 310.7 µs |
| Node.js | server | http | yes | 16 KiB | 243.1 µs | 239.7 µs | 284.4 µs | 339.2 µs |
| Go | server | http | no | 16 KiB | 188.5 µs | 184.7 µs | 231.5 µs | 278.8 µs |
| Go | server | http | yes | 16 KiB | 204.6 µs | 200.0 µs | 245.7 µs | 294.0 µs |
| Dart | server | http | no | 64 KiB | 257.5 µs | 250.2 µs | 324.1 µs | 382.2 µs |
| Dart | server | http | yes | 64 KiB | 1.57 ms | 1.54 ms | 1.74 ms | 1.88 ms |
| Node.js | server | http | no | 64 KiB | 253.7 µs | 248.2 µs | 300.2 µs | 370.4 µs |
| Node.js | server | http | yes | 64 KiB | 327.5 µs | 316.6 µs | 389.7 µs | 500.6 µs |
| Go | server | http | no | 64 KiB | 214.4 µs | 207.9 µs | 264.4 µs | 321.6 µs |
| Go | server | http | yes | 64 KiB | 254.1 µs | 247.5 µs | 308.6 µs | 376.1 µs |
| Dart | server | http | no | 1 MiB | 1.71 ms | 1.60 ms | 2.58 ms | 2.91 ms |
| Dart | server | http | yes | 1 MiB | 21.36 ms | 21.22 ms | 22.78 ms | 23.36 ms |
| Node.js | server | http | no | 1 MiB | 777.9 µs | 670.1 µs | 994.7 µs | 4.67 ms |
| Node.js | server | http | yes | 1 MiB | 1.51 ms | 1.47 ms | 1.74 ms | 2.07 ms |
| Go | server | http | no | 1 MiB | 788.0 µs | 770.8 µs | 932.0 µs | 1.06 ms |
| Go | server | http | yes | 1 MiB | 1.58 ms | 1.55 ms | 1.89 ms | 2.14 ms |
| Dart | client | io | no | 1 KiB | 104.4 µs | 99.0 µs | 137.0 µs | 164.0 µs |
| Dart | client | io | yes | 1 KiB | 215.5 µs | 209.0 µs | 274.0 µs | 329.0 µs |
| Node.js | client | io | no | 1 KiB | 89.5 µs | 89.8 µs | 113.9 µs | 139.2 µs |
| Node.js | client | io | yes | 1 KiB | 96.8 µs | 92.9 µs | 129.0 µs | 153.7 µs |
| Go | client | io | no | 1 KiB | 87.2 µs | 87.2 µs | 111.7 µs | 138.8 µs |
| Go | client | io | yes | 1 KiB | 91.7 µs | 90.5 µs | 118.7 µs | 144.5 µs |
| Dart | client | io | no | 16 KiB | 114.0 µs | 108.0 µs | 151.0 µs | 187.0 µs |
| Dart | client | io | yes | 16 KiB | 479.2 µs | 475.0 µs | 545.0 µs | 622.0 µs |
| Node.js | client | io | no | 16 KiB | 93.6 µs | 91.3 µs | 118.0 µs | 144.8 µs |
| Node.js | client | io | yes | 16 KiB | 134.1 µs | 132.8 µs | 164.1 µs | 194.9 µs |
| Go | client | io | no | 16 KiB | 88.6 µs | 88.2 µs | 112.8 µs | 139.3 µs |
| Go | client | io | yes | 16 KiB | 113.2 µs | 106.9 µs | 146.8 µs | 172.3 µs |
| Dart | client | io | no | 64 KiB | 146.6 µs | 142.0 µs | 191.0 µs | 231.0 µs |
| Dart | client | io | yes | 64 KiB | 1.29 ms | 1.28 ms | 1.40 ms | 1.48 ms |
| Node.js | client | io | no | 64 KiB | 113.3 µs | 99.6 µs | 144.3 µs | 177.1 µs |
| Node.js | client | io | yes | 64 KiB | 194.6 µs | 179.2 µs | 236.9 µs | 292.1 µs |
| Go | client | io | no | 64 KiB | 99.5 µs | 94.8 µs | 136.0 µs | 164.3 µs |
| Go | client | io | yes | 64 KiB | 169.6 µs | 170.2 µs | 217.8 µs | 262.0 µs |
| Dart | client | io | no | 1 MiB | 947.5 µs | 797.0 µs | 1.33 ms | 4.89 ms |
| Dart | client | io | yes | 1 MiB | 16.69 ms | 16.64 ms | 17.16 ms | 17.61 ms |
| Node.js | client | io | no | 1 MiB | 421.0 µs | 309.0 µs | 696.0 µs | 3.87 ms |
| Node.js | client | io | yes | 1 MiB | 1.42 ms | 1.42 ms | 1.66 ms | 1.94 ms |
| Go | client | io | no | 1 MiB | 190.8 µs | 181.6 µs | 234.2 µs | 291.1 µs |
| Go | client | io | yes | 1 MiB | 1.01 ms | 973.3 µs | 1.26 ms | 1.55 ms |
| Dart | client | http | no | 1 KiB | 206.9 µs | 200.0 µs | 257.0 µs | 308.0 µs |
| Dart | client | http | yes | 1 KiB | 330.7 µs | 320.0 µs | 404.0 µs | 456.0 µs |
| Node.js | client | http | no | 1 KiB | 192.1 µs | 185.4 µs | 231.5 µs | 273.9 µs |
| Node.js | client | http | yes | 1 KiB | 216.9 µs | 207.1 µs | 264.9 µs | 312.7 µs |
| Go | client | http | no | 1 KiB | 152.0 µs | 150.8 µs | 186.1 µs | 214.2 µs |
| Go | client | http | yes | 1 KiB | 161.4 µs | 158.9 µs | 195.5 µs | 224.0 µs |
| Dart | client | http | no | 16 KiB | 223.4 µs | 218.0 µs | 278.0 µs | 324.0 µs |
| Dart | client | http | yes | 16 KiB | 659.7 µs | 647.0 µs | 770.0 µs | 840.0 µs |
| Node.js | client | http | no | 16 KiB | 212.3 µs | 203.5 µs | 259.5 µs | 315.2 µs |
| Node.js | client | http | yes | 16 KiB | 253.3 µs | 241.5 µs | 304.0 µs | 363.1 µs |
| Go | client | http | no | 16 KiB | 181.0 µs | 177.1 µs | 222.4 µs | 260.5 µs |
| Go | client | http | yes | 16 KiB | 184.1 µs | 179.1 µs | 224.3 µs | 259.6 µs |
| Dart | client | http | no | 64 KiB | 244.7 µs | 238.0 µs | 317.0 µs | 371.0 µs |
| Dart | client | http | yes | 64 KiB | 1.92 ms | 1.91 ms | 2.14 ms | 2.27 ms |
| Node.js | client | http | no | 64 KiB | 270.6 µs | 250.6 µs | 331.3 µs | 428.8 µs |
| Node.js | client | http | yes | 64 KiB | 356.2 µs | 338.2 µs | 426.0 µs | 539.0 µs |
| Go | client | http | no | 64 KiB | 198.8 µs | 194.8 µs | 239.3 µs | 275.7 µs |
| Go | client | http | yes | 64 KiB | 244.3 µs | 232.3 µs | 324.0 µs | 372.7 µs |
| Dart | client | http | no | 1 MiB | 1.61 ms | 1.56 ms | 2.26 ms | 2.55 ms |
| Dart | client | http | yes | 1 MiB | 25.82 ms | 25.64 ms | 27.40 ms | 27.86 ms |
| Node.js | client | http | no | 1 MiB | 1.11 ms | 921.1 µs | 2.14 ms | 5.02 ms |
| Node.js | client | http | yes | 1 MiB | 1.82 ms | 1.77 ms | 2.23 ms | 2.87 ms |
| Go | client | http | no | 1 MiB | 689.4 µs | 660.9 µs | 848.5 µs | 995.1 µs |
| Go | client | http | yes | 1 MiB | 1.64 ms | 1.53 ms | 2.33 ms | 3.10 ms |

<a id="absolute-8-kib-cgroup-memory"></a>
### Cgroup memory

| Target | Role | Path | TLS | Payload | Current | Peak |
|---|---|---|---:|---:|---:|---:|
| Dart | server | io | no | 1 KiB | 9.2 MiB | 9.3 MiB |
| Dart | server | io | yes | 1 KiB | 12.7 MiB | 13.0 MiB |
| Node.js | server | io | no | 1 KiB | 21.4 MiB | 21.9 MiB |
| Node.js | server | io | yes | 1 KiB | 21.5 MiB | 22.4 MiB |
| Go | server | io | no | 1 KiB | 2.5 MiB | 6.2 MiB |
| Go | server | io | yes | 1 KiB | 7.5 MiB | 7.8 MiB |
| Dart | server | io | no | 16 KiB | 10.1 MiB | 10.9 MiB |
| Dart | server | io | yes | 16 KiB | 8.9 MiB | 9.6 MiB |
| Node.js | server | io | no | 16 KiB | 60.4 MiB | 64.9 MiB |
| Node.js | server | io | yes | 16 KiB | 56.4 MiB | 58.8 MiB |
| Go | server | io | no | 16 KiB | 3.0 MiB | 6.2 MiB |
| Go | server | io | yes | 16 KiB | 7.5 MiB | 7.9 MiB |
| Dart | server | io | no | 64 KiB | 15.9 MiB | 40.1 MiB |
| Dart | server | io | yes | 64 KiB | 8.5 MiB | 9.1 MiB |
| Node.js | server | io | no | 64 KiB | 85.5 MiB | 94.2 MiB |
| Node.js | server | io | yes | 64 KiB | 55.5 MiB | 58.3 MiB |
| Go | server | io | no | 64 KiB | 2.9 MiB | 6.2 MiB |
| Go | server | io | yes | 64 KiB | 7.4 MiB | 8.2 MiB |
| Dart | server | io | no | 1 MiB | 87.4 MiB | 190.2 MiB |
| Dart | server | io | yes | 1 MiB | 9.0 MiB | 9.5 MiB |
| Node.js | server | io | no | 1 MiB | 86.0 MiB | 94.3 MiB |
| Node.js | server | io | yes | 1 MiB | 50.7 MiB | 55.1 MiB |
| Go | server | io | no | 1 MiB | 3.2 MiB | 10.1 MiB |
| Go | server | io | yes | 1 MiB | 7.2 MiB | 14.4 MiB |
| Dart | server | http | no | 1 KiB | 7.8 MiB | 8.4 MiB |
| Dart | server | http | yes | 1 KiB | 10.6 MiB | 10.9 MiB |
| Node.js | server | http | no | 1 KiB | 25.1 MiB | 26.6 MiB |
| Node.js | server | http | yes | 1 KiB | 36.1 MiB | 36.1 MiB |
| Go | server | http | no | 1 KiB | 7.5 MiB | 7.8 MiB |
| Go | server | http | yes | 1 KiB | 8.6 MiB | 8.9 MiB |
| Dart | server | http | no | 16 KiB | 7.9 MiB | 8.6 MiB |
| Dart | server | http | yes | 16 KiB | 12.2 MiB | 12.5 MiB |
| Node.js | server | http | no | 16 KiB | 30.2 MiB | 31.2 MiB |
| Node.js | server | http | yes | 16 KiB | 50.8 MiB | 51.5 MiB |
| Go | server | http | no | 16 KiB | 7.8 MiB | 8.5 MiB |
| Go | server | http | yes | 16 KiB | 8.3 MiB | 9.3 MiB |
| Dart | server | http | no | 64 KiB | 10.5 MiB | 11.3 MiB |
| Dart | server | http | yes | 64 KiB | 20.4 MiB | 21.1 MiB |
| Node.js | server | http | no | 64 KiB | 34.7 MiB | 40.9 MiB |
| Node.js | server | http | yes | 64 KiB | 54.3 MiB | 56.9 MiB |
| Go | server | http | no | 64 KiB | 7.4 MiB | 8.6 MiB |
| Go | server | http | yes | 64 KiB | 8.1 MiB | 9.1 MiB |
| Dart | server | http | no | 1 MiB | 85.8 MiB | 172.3 MiB |
| Dart | server | http | yes | 1 MiB | 22.3 MiB | 23.8 MiB |
| Node.js | server | http | no | 1 MiB | 112.5 MiB | 120.7 MiB |
| Node.js | server | http | yes | 1 MiB | 125.3 MiB | 140.9 MiB |
| Go | server | http | no | 1 MiB | 6.6 MiB | 13.3 MiB |
| Go | server | http | yes | 1 MiB | 7.2 MiB | 15.5 MiB |
| Dart | client | io | no | 1 KiB | 24.7 MiB | 25.2 MiB |
| Dart | client | io | yes | 1 KiB | 17.8 MiB | 18.0 MiB |
| Node.js | client | io | no | 1 KiB | 169.9 MiB | 211.1 MiB |
| Node.js | client | io | yes | 1 KiB | 171.5 MiB | 197.8 MiB |
| Go | client | io | no | 1 KiB | 44.5 MiB | 47.0 MiB |
| Go | client | io | yes | 1 KiB | 61.8 MiB | 67.7 MiB |
| Dart | client | io | no | 16 KiB | 25.4 MiB | 26.3 MiB |
| Dart | client | io | yes | 16 KiB | 11.4 MiB | 11.5 MiB |
| Node.js | client | io | no | 16 KiB | 128.0 MiB | 152.0 MiB |
| Node.js | client | io | yes | 16 KiB | 108.7 MiB | 123.2 MiB |
| Go | client | io | no | 16 KiB | 36.3 MiB | 36.6 MiB |
| Go | client | io | yes | 16 KiB | 31.9 MiB | 32.2 MiB |
| Dart | client | io | no | 64 KiB | 77.1 MiB | 168.7 MiB |
| Dart | client | io | yes | 64 KiB | 8.9 MiB | 11.1 MiB |
| Node.js | client | io | no | 64 KiB | 107.8 MiB | 107.8 MiB |
| Node.js | client | io | yes | 64 KiB | 104.7 MiB | 104.7 MiB |
| Go | client | io | no | 64 KiB | 26.3 MiB | 28.8 MiB |
| Go | client | io | yes | 64 KiB | 10.5 MiB | 11.3 MiB |
| Dart | client | io | no | 1 MiB | 87.7 MiB | 184.3 MiB |
| Dart | client | io | yes | 1 MiB | 8.9 MiB | 13.8 MiB |
| Node.js | client | io | no | 1 MiB | 91.7 MiB | 96.6 MiB |
| Node.js | client | io | yes | 1 MiB | 104.8 MiB | 115.1 MiB |
| Go | client | io | no | 1 MiB | 7.5 MiB | 15.7 MiB |
| Go | client | io | yes | 1 MiB | 7.3 MiB | 14.4 MiB |
| Dart | client | http | no | 1 KiB | 9.7 MiB | 11.0 MiB |
| Dart | client | http | yes | 1 KiB | 11.2 MiB | 11.9 MiB |
| Node.js | client | http | no | 1 KiB | 53.8 MiB | 54.8 MiB |
| Node.js | client | http | yes | 1 KiB | 58.7 MiB | 59.0 MiB |
| Go | client | http | no | 1 KiB | 12.3 MiB | 17.5 MiB |
| Go | client | http | yes | 1 KiB | 11.4 MiB | 15.7 MiB |
| Dart | client | http | no | 16 KiB | 10.2 MiB | 11.6 MiB |
| Dart | client | http | yes | 16 KiB | 11.8 MiB | 12.8 MiB |
| Node.js | client | http | no | 16 KiB | 55.3 MiB | 61.8 MiB |
| Node.js | client | http | yes | 16 KiB | 72.2 MiB | 72.2 MiB |
| Go | client | http | no | 16 KiB | 8.7 MiB | 11.7 MiB |
| Go | client | http | yes | 16 KiB | 8.3 MiB | 10.8 MiB |
| Dart | client | http | no | 64 KiB | 11.2 MiB | 12.9 MiB |
| Dart | client | http | yes | 64 KiB | 19.0 MiB | 19.6 MiB |
| Node.js | client | http | no | 64 KiB | 89.6 MiB | 99.5 MiB |
| Node.js | client | http | yes | 64 KiB | 74.8 MiB | 78.9 MiB |
| Go | client | http | no | 64 KiB | 7.8 MiB | 11.4 MiB |
| Go | client | http | yes | 64 KiB | 8.1 MiB | 12.0 MiB |
| Dart | client | http | no | 1 MiB | 64.5 MiB | 174.4 MiB |
| Dart | client | http | yes | 1 MiB | 20.3 MiB | 22.6 MiB |
| Node.js | client | http | no | 1 MiB | 141.6 MiB | 149.7 MiB |
| Node.js | client | http | yes | 1 MiB | 149.5 MiB | 165.7 MiB |
| Go | client | http | no | 1 MiB | 7.0 MiB | 11.4 MiB |
| Go | client | http | yes | 1 MiB | 7.0 MiB | 16.9 MiB |

## Dart TLS buffer-size sweep absolute results (1 MiB payload)

<a id="absolute-dart-buffer-sweep-qps"></a>
### QPS and variability

| Role | Path | Buffer | QPS median | QPS min | QPS max | CV |
|---|---|---:|---:|---:|---:|---:|
| server | io | 8 KiB | 41 | 41 | 41 | 0.7% |
| server | io | 32 KiB | 107 | 105 | 110 | 1.9% |
| server | io | 128 KiB | 174 | 173 | 174 | 0.4% |
| server | io | 512 KiB | 152 | 148 | 153 | 1.5% |
| server | io | 1 MiB | 140 | 138 | 140 | 0.6% |
| server | http | 8 KiB | 63 | 60 | 63 | 2.3% |
| server | http | 32 KiB | 184 | 183 | 188 | 1.2% |
| server | http | 128 KiB | 327 | 326 | 330 | 0.5% |
| server | http | 512 KiB | 348 | 342 | 352 | 1.1% |
| server | http | 1 MiB | 365 | 340 | 374 | 4.1% |
| client | io | 8 KiB | 95 | 95 | 97 | 0.7% |
| client | io | 32 KiB | 282 | 275 | 289 | 2.1% |
| client | io | 128 KiB | 342 | 332 | 342 | 1.3% |
| client | io | 512 KiB | 302 | 279 | 325 | 6.2% |
| client | io | 1 MiB | 294 | 283 | 331 | 6.8% |
| client | http | 8 KiB | 50 | 49 | 51 | 1.6% |
| client | http | 32 KiB | 145 | 145 | 146 | 0.4% |
| client | http | 128 KiB | 261 | 255 | 265 | 1.5% |
| client | http | 512 KiB | 265 | 264 | 274 | 1.6% |
| client | http | 1 MiB | 267 | 260 | 281 | 3.2% |

<a id="absolute-dart-buffer-sweep-target-cpu"></a>
### Target CPU

| Role | Path | Buffer | CPU ns/op | User ns/op | System ns/op | Target CPU |
|---|---|---:|---:|---:|---:|---:|
| server | io | 8 KiB | 24,020,563 | 9,086,326 | 15,140,406 | 96.9% |
| server | io | 32 KiB | 9,336,487 | 3,656,307 | 5,680,179 | 97.1% |
| server | io | 128 KiB | 5,745,928 | 2,324,304 | 3,417,389 | 96.7% |
| server | io | 512 KiB | 6,575,822 | 2,567,321 | 4,056,593 | 96.9% |
| server | io | 1 MiB | 7,128,982 | 2,757,403 | 4,397,886 | 96.5% |
| server | http | 8 KiB | 15,816,068 | 6,950,219 | 8,904,754 | 96.7% |
| server | http | 32 KiB | 5,413,232 | 2,542,801 | 2,870,431 | 96.7% |
| server | http | 128 KiB | 3,052,979 | 1,574,237 | 1,477,832 | 97.1% |
| server | http | 512 KiB | 2,868,986 | 1,772,347 | 1,108,765 | 97.5% |
| server | http | 1 MiB | 2,740,290 | 1,801,906 | 945,476 | 96.7% |
| client | io | 8 KiB | 10,474,372 | 4,859,467 | 5,617,050 | 96.9% |
| client | io | 32 KiB | 3,547,319 | 1,786,840 | 1,764,740 | 97.2% |
| client | io | 128 KiB | 2,925,465 | 1,464,754 | 1,489,098 | 97.1% |
| client | io | 512 KiB | 3,302,077 | 1,514,249 | 1,809,438 | 97.2% |
| client | io | 1 MiB | 3,392,119 | 1,555,371 | 1,836,747 | 96.9% |
| client | http | 8 KiB | 19,740,511 | 7,914,349 | 11,568,852 | 97.0% |
| client | http | 32 KiB | 6,869,370 | 3,080,497 | 3,788,857 | 96.9% |
| client | http | 128 KiB | 3,820,649 | 1,824,964 | 1,950,642 | 97.5% |
| client | http | 512 KiB | 3,766,669 | 2,095,695 | 1,611,490 | 97.2% |
| client | http | 1 MiB | 3,741,604 | 2,254,443 | 1,487,161 | 97.3% |

<a id="absolute-dart-buffer-sweep-latency"></a>
### Latency

| Role | Path | Buffer | Mean | p50 | p95 | p99 |
|---|---|---:|---:|---:|---:|---:|
| server | io | 8 KiB | 24.68 ms | 24.40 ms | 26.17 ms | 26.87 ms |
| server | io | 32 KiB | 9.52 ms | 9.46 ms | 10.13 ms | 10.43 ms |
| server | io | 128 KiB | 6.74 ms | 6.71 ms | 7.26 ms | 7.53 ms |
| server | io | 512 KiB | 7.08 ms | 7.04 ms | 7.81 ms | 8.17 ms |
| server | io | 1 MiB | 7.36 ms | 7.35 ms | 8.06 ms | 8.40 ms |
| server | http | 8 KiB | 21.36 ms | 21.22 ms | 22.78 ms | 23.36 ms |
| server | http | 32 KiB | 6.78 ms | 6.74 ms | 7.29 ms | 7.59 ms |
| server | http | 128 KiB | 4.60 ms | 4.56 ms | 5.07 ms | 5.31 ms |
| server | http | 512 KiB | 4.09 ms | 4.06 ms | 4.56 ms | 4.87 ms |
| server | http | 1 MiB | 4.33 ms | 4.29 ms | 4.80 ms | 5.28 ms |
| client | io | 8 KiB | 16.69 ms | 16.64 ms | 17.16 ms | 17.61 ms |
| client | io | 32 KiB | 5.38 ms | 5.35 ms | 5.67 ms | 5.95 ms |
| client | io | 128 KiB | 3.66 ms | 3.62 ms | 4.25 ms | 4.44 ms |
| client | io | 512 KiB | 3.92 ms | 3.89 ms | 4.44 ms | 4.66 ms |
| client | io | 1 MiB | 3.98 ms | 3.95 ms | 4.59 ms | 5.12 ms |
| client | http | 8 KiB | 25.82 ms | 25.64 ms | 27.40 ms | 27.86 ms |
| client | http | 32 KiB | 8.05 ms | 8.01 ms | 8.60 ms | 8.88 ms |
| client | http | 128 KiB | 5.07 ms | 5.07 ms | 5.67 ms | 6.01 ms |
| client | http | 512 KiB | 4.56 ms | 4.54 ms | 5.20 ms | 5.51 ms |
| client | http | 1 MiB | 4.92 ms | 4.86 ms | 5.74 ms | 6.18 ms |

<a id="absolute-dart-buffer-sweep-cgroup-memory"></a>
### Cgroup memory

| Role | Path | Buffer | Current | Peak |
|---|---|---:|---:|---:|
| server | io | 8 KiB | 9.0 MiB | 9.5 MiB |
| server | io | 32 KiB | 9.8 MiB | 10.4 MiB |
| server | io | 128 KiB | 10.2 MiB | 11.4 MiB |
| server | io | 512 KiB | 15.9 MiB | 17.2 MiB |
| server | io | 1 MiB | 19.1 MiB | 22.9 MiB |
| server | http | 8 KiB | 22.3 MiB | 23.8 MiB |
| server | http | 32 KiB | 31.9 MiB | 33.8 MiB |
| server | http | 128 KiB | 25.7 MiB | 50.0 MiB |
| server | http | 512 KiB | 17.2 MiB | 50.3 MiB |
| server | http | 1 MiB | 24.4 MiB | 76.6 MiB |
| client | io | 8 KiB | 8.9 MiB | 13.8 MiB |
| client | io | 32 KiB | 9.8 MiB | 14.7 MiB |
| client | io | 128 KiB | 10.2 MiB | 16.9 MiB |
| client | io | 512 KiB | 11.2 MiB | 20.4 MiB |
| client | io | 1 MiB | 15.1 MiB | 27.5 MiB |
| client | http | 8 KiB | 20.3 MiB | 22.6 MiB |
| client | http | 32 KiB | 26.6 MiB | 28.9 MiB |
| client | http | 128 KiB | 25.2 MiB | 51.4 MiB |
| client | http | 512 KiB | 14.4 MiB | 52.3 MiB |
| client | http | 1 MiB | 20.2 MiB | 81.3 MiB |
