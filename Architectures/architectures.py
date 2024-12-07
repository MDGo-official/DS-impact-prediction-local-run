import torch
from torch import nn

class VS_SM(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(3, 25, 13, padding=6)
        self.conv2 = nn.Conv1d(25, 25, 11, padding=5)
        self.conv3 = nn.Conv1d(25, 50, 9, padding=4)
        self.conv4 = nn.Conv1d(50, 50, 7, padding=3)
        self.conv5 = nn.Conv1d(50, 50, 5, padding=2)
        self.batchNorm1 = nn.BatchNorm1d(50)
        self.lstm1 = nn.LSTM(50, 50, batch_first=True)
        self.conv6 = nn.Conv1d(50, 60, 5, padding=2)
        self.conv7 = nn.Conv1d(60, 60, 5, padding=2)
        self.conv8 = nn.Conv1d(60, 60, 3, padding=1)
        self.batchNorm2 = nn.BatchNorm1d(60)
        self.lstm2 = nn.LSTM(60, 60, batch_first=True, bidirectional=True)
        self.conv9 = nn.Conv1d(120, 120, 5, padding=2)
        self.conv10 = nn.Conv1d(120, 120, 3, padding=1)
        self.conv11 = nn.Conv1d(120, 60, 3, padding=1)
        self.conv12 = nn.Conv1d(60, 1, 3, padding=1)
        self.leaky_relu = nn.LeakyReLU(inplace=True)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x = self.leaky_relu(self.conv1(x))
        x = self.leaky_relu(self.conv2(x))
        x = self.leaky_relu(self.conv3(x))
        x = self.leaky_relu(self.conv4(x))
        x = self.leaky_relu(self.conv5(x))
        x = self.batchNorm1(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm1(x)
        x = x.permute(0, 2, 1)
        x = self.leaky_relu(self.conv6(x))
        x = self.leaky_relu(self.conv7(x))
        x = self.leaky_relu(self.conv8(x))
        x = self.batchNorm2(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm2(x)
        x = x.permute(0, 2, 1)
        x = self.leaky_relu(self.conv9(x))
        x = self.leaky_relu(self.conv10(x))
        x = self.leaky_relu(self.conv11(x))
        x = self.relu(self.conv12(x))
        return x


class VS_SM_hip(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(3, 25, 13, padding=6)
        self.conv2 = nn.Conv1d(25, 25, 11, padding=5)
        self.conv3 = nn.Conv1d(25, 50, 9, padding=4)
        self.conv4 = nn.Conv1d(50, 50, 7, padding=3)
        self.conv5 = nn.Conv1d(50, 50, 5, padding=2)
        self.batchNorm1 = nn.BatchNorm1d(50)
        self.lstm1 = nn.LSTM(50, 50, batch_first=True)
        self.conv6 = nn.Conv1d(50, 60, 5, padding=2)
        self.conv7 = nn.Conv1d(60, 60, 5, padding=2)
        self.conv8 = nn.Conv1d(60, 60, 3, padding=1)
        self.batchNorm2 = nn.BatchNorm1d(60)
        self.lstm2 = nn.LSTM(60, 60, batch_first=True, bidirectional=True)
        self.conv9 = nn.Conv1d(120, 100, 5, padding=2)
        self.conv9_1 = nn.Conv1d(120, 1, 1, padding=0)
        self.fc9_1 = nn.Linear(100, 1)
        self.conv10 = nn.Conv1d(100, 70, 3, padding=1)
        self.conv11 = nn.Conv1d(70, 40, 3, padding=1)
        self.conv12 = nn.Conv1d(40, 1, 1, padding=0)
        self.leaky_relu = nn.LeakyReLU(inplace=True)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x = self.leaky_relu(self.conv1(x))
        x = self.leaky_relu(self.conv2(x))
        x = self.leaky_relu(self.conv3(x))
        x = self.leaky_relu(self.conv4(x))
        x = self.leaky_relu(self.conv5(x))
        x = self.batchNorm1(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm1(x)
        x = x.permute(0, 2, 1)
        x = self.leaky_relu(self.conv6(x))
        x = self.leaky_relu(self.conv7(x))
        x = self.leaky_relu(self.conv8(x))
        x = self.batchNorm2(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm2(x)
        x = x.permute(0, 2, 1)
        bric = self.leaky_relu(self.conv9_1(x))
        bric = bric.reshape(bric.size(0), -1)
        bric = self.relu(self.fc9_1(bric))
        x = self.leaky_relu(self.conv9(x))
        x = self.leaky_relu(self.conv10(x))
        x = self.leaky_relu(self.conv11(x))
        x = self.relu(self.conv12(x))
        x2 = torch.max(x, dim=-1,)
        return x, bric

class Damages_model(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 25, 7, padding=3)
        self.conv2 = nn.Conv1d(25, 25, 7, padding=3)
        self.lstm1 = nn.LSTM(25, 25, batch_first=True, bidirectional=True)
        self.conv3 = nn.Conv1d(50, 50, 5, stride=2, padding=2)
        self.conv4 = nn.Conv1d(50, 50, 5, padding=2)
        self.conv5 = nn.Conv1d(50, 100, 3, stride=2, padding=1)
        self.batchNorm1 = nn.BatchNorm1d(100)
        # self.lstm2 = nn.LSTM(100, 100, batch_first=True, bidirectional=True)
        self.conv6 = nn.Conv1d(100, 256, 5, padding=0)
        self.conv7 = nn.Conv1d(256, 256, 3, padding=0)
        self.conv8 = nn.Conv1d(256, 256, 3, padding=0)
        self.batchNorm2 = nn.BatchNorm1d(256)
        self.conv9 = nn.Conv1d(256, 256, 3, padding=1)
        self.fc10 = nn.Linear(256 * 16, 1024)
        self.dropout10 = nn.Dropout(p=0.5)
        self.fc11 = nn.Linear(1024, 156)  # 234, without sim 212,
        self.leaky_relu = nn.LeakyReLU(inplace=True)
        self.relu = nn.ReLU(inplace=False)

    def forward(self, x):
        x = self.leaky_relu(self.conv1(x))
        x = self.leaky_relu(self.conv2(x))
        x = x.permute(0, 2, 1)
        x, _ = self.lstm1(x)
        x = x.permute(0, 2, 1)
        x = self.leaky_relu(self.conv3(x))
        x = self.leaky_relu(self.conv4(x))
        x = self.leaky_relu(self.conv5(x))
        x = self.batchNorm1(x)
        x = self.leaky_relu(self.conv6(x))
        x = self.leaky_relu(self.conv7(x))
        x = self.leaky_relu(self.conv8(x))
        x = self.batchNorm2(x)
        x = self.leaky_relu(self.conv9(x))
        x = self.leaky_relu(self.fc10(x.reshape(-1, 256 * 16)))
        x = self.dropout10(x)
        x = self.relu(self.fc11(x))
        return x


class InceptionModule(nn.Module):
    """
    Module build backbone on architecture from article "InceptionTime: Finding AlexNet for Time Series
Classification", https://arxiv.org/abs/1909.04939
    """
    def __init__(self, ni=2, nf=16, ks=40, n_ks=4, bottleneck=True, activation='relu'):
        super().__init__()
        if isinstance(ks, int):
            ks = [ks // (2 ** i) for i in range(n_ks)]
        ks = [k if k % 2 != 0 else k - 1 for k in ks]  # ensure odd ks
        if activation == 'relu':
            self.act = nn.ReLU()
        else:
            self.act = nn.LeakyReLU()
        bottleneck = bottleneck if ni > 2 else False
        self.batchNorm1 = nn.BatchNorm1d(ni)
        self.bottleneck = nn.Conv1d(in_channels=ni, out_channels=nf, kernel_size=1) if bottleneck else nn.Identity()
        self.convs = nn.ModuleList([nn.Conv1d(nf if bottleneck else ni, nf, k, padding=k // 2) for k in ks])
        self.maxconvpool = nn.Sequential(*[nn.MaxPool1d(3, stride=1, padding=1), nn.Conv1d(ni, nf, 1)])
        self.batchNorm2 = nn.BatchNorm1d(nf * (len(ks) + 1))

    def forward(self, x):
        input_tensor = self.batchNorm1(x)
        x = self.bottleneck(input_tensor)
        x = torch.cat(([l(x) for l in self.convs] + [self.maxconvpool(input_tensor)]), dim=1)
        x = self.act(self.batchNorm2(x))
        return x


class InceptionBlockBase(nn.Module):
    """
        Module build the architecture from the article "InceptionTime: Finding AlexNet for Time Series
    Classification", https://arxiv.org/abs/1909.04939
    """
    def __init__(self, ni=2, nf=16, residual=True, depth=4, ks=40, n_ks=4, bottleneck=True, activation='relu', avp=1,
                 GAP=True):
        super().__init__()
        self.residual, self.depth = residual, depth
        self.inception, self.shortcut, self.resconv = nn.ModuleList(), nn.ModuleList(), nn.ModuleList()
        if activation == 'relu':
            self.act = nn.ReLU()
        else:
            self.act = nn.LeakyReLU()
        for d in range(depth):
            self.inception.append(
                InceptionModule(ni if d == 0 else nf * (n_ks + 1), nf, ks, n_ks, bottleneck, activation))
            if self.residual and d % 2 == 1:
                n_in, n_out = ni if d == 1 else nf * (n_ks + 1), nf * (n_ks + 1)
                self.shortcut.append(nn.BatchNorm1d(n_in))
                self.resconv.append(nn.Conv1d(n_in + nf * (n_ks + 1), n_out, 1))
        if GAP:
            self.GAP = nn.AdaptiveAvgPool1d(avp)
        else:
            self.GAP = nn.Identity()

    def forward(self, x):
        res = x
        for d, l in enumerate(range(self.depth)):
            x = self.inception[d](x)
            if self.residual and d % 2 == 1:
                x = torch.cat((x, self.shortcut[d // 2](res)), dim=1)
                x = res = self.act(self.resconv[d // 2](x))
        x = self.GAP(x)
        return x


class InceptionBlockMultiInput(nn.Module):
    """
    Architecture based on "InceptionTime: Finding AlexNet for Time Series
    Classification", https://arxiv.org/abs/1909.04939. The difference are multi-input (3 signals) and concatination of
     the output of the outputs backbone models
    """
    def __init__(self, ni=2, nf=16, residual=True, depth=4, ks=40, n_ks=3, bottleneck=True, activation='relu', avp=1,
                 dropout_p=0):
        super().__init__()
        self.inseption1 = InceptionBlockBase(ni, nf, residual, depth, ks, n_ks, bottleneck, activation, avp)
        self.inseption2 = InceptionBlockBase(ni, nf, residual, depth, ks + 5, n_ks, bottleneck, activation, avp)
        self.inseption3 = InceptionBlockBase(ni, nf, residual, depth, ks + 10, n_ks, bottleneck, activation, avp)
        self.conv1 = nn.Conv1d(3, 1, 1)
        self.leaky_relu = nn.LeakyReLU()
        self.dropout = nn.Dropout(dropout_p)
        self.fc1 = nn.Linear(1 * nf * (n_ks + 1) * avp, 2)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x0 = self.inseption1(x[0])
        x1 = self.inseption2(x[1])
        x2 = self.inseption3(x[2])
        x = torch.cat([x0, x1, x2], dim=-1)
        x = self.leaky_relu(self.conv1(x.view(-1, x.shape[2], x.shape[1])))
        x = x.view(-1, x.shape[1] * x.shape[2])
        x = self.dropout(x)
        x = self.fc1(x)
        out = self.softmax(x)
        return x, out
